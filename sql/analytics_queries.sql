-- =====================================================================
-- Consultas analíticas del portfolio de e-commerce
--
-- Tabla: orders (
--     order_id, customer_id, order_date, category, region,
--     payment_method, price, shipping_days, review_score
-- )
--
-- Dialecto: SQL estándar para PostgreSQL / DuckDB.
-- SQLite: para la consulta (d) sustituir la resta de fechas por
--         julianday(order_date) - julianday(previous_order_date).
-- =====================================================================


-- ---------------------------------------------------------------------
-- (a) ¿Qué categorías concentran los ingresos y con qué peso relativo?
--
-- Pregunta de negocio: identificar las categorías que sostienen la
-- facturación para priorizar inventario y campañas.
-- Grano: una fila por categoría.
-- ---------------------------------------------------------------------
WITH category_revenue AS (
    SELECT
        category,
        COUNT(*) AS orders_count,
        SUM(price) AS revenue
    FROM orders
    WHERE price IS NOT NULL
    GROUP BY category
),
ranked AS (
    SELECT
        category,
        orders_count,
        revenue,
        SUM(revenue) OVER () AS total_revenue,
        ROUND(100.0 * revenue / NULLIF(SUM(revenue) OVER (), 0), 2) AS share_pct
    FROM category_revenue
)
SELECT
    category,
    orders_count,
    ROUND(revenue, 2) AS revenue,
    share_pct,
    DENSE_RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM ranked
ORDER BY revenue DESC;


-- ---------------------------------------------------------------------
-- (b) ¿Quiénes son los 3 clientes que más gastan en cada región?
--
-- Pregunta de negocio: detectar clientes de alto valor por zona para
-- programas de fidelización y atención personalizada.
-- Grano: una fila por cliente y región.
-- Nota: DENSE_RANK conserva empates, por lo que puede devolver más de
--       tres filas por región si hay importes idénticos.
-- ---------------------------------------------------------------------
WITH customer_region_spend AS (
    SELECT
        customer_id,
        region,
        COUNT(*) AS orders_count,
        SUM(price) AS total_spend
    FROM orders
    WHERE price IS NOT NULL
      AND region IS NOT NULL
    GROUP BY customer_id, region
),
ranked AS (
    SELECT
        customer_id,
        region,
        orders_count,
        total_spend,
        DENSE_RANK() OVER (
            PARTITION BY region
            ORDER BY total_spend DESC
        ) AS rank_in_region
    FROM customer_region_spend
)
SELECT
    region,
    rank_in_region,
    customer_id,
    orders_count,
    ROUND(total_spend, 2) AS total_spend
FROM ranked
WHERE rank_in_region <= 3
ORDER BY region, rank_in_region;


-- ---------------------------------------------------------------------
-- (c) ¿Cuánto cae la satisfacción cuando el envío llega tarde?
--
-- Pregunta de negocio: cuantificar el impacto de la logística en la
-- reseña del cliente y justificar inversión en tiempos de entrega.
-- Grano: una fila por estado de entrega (a tiempo / retrasada).
-- ---------------------------------------------------------------------
WITH classified_orders AS (
    SELECT
        CASE
            WHEN shipping_days <= 6 THEN 'A tiempo'
            ELSE 'Retrasada'
        END AS delivery_status,
        review_score
    FROM orders
    WHERE shipping_days IS NOT NULL
      AND review_score IS NOT NULL
)
SELECT
    delivery_status,
    COUNT(*) AS orders_count,
    ROUND(AVG(review_score), 2) AS avg_review_score,
    ROUND(100.0 * AVG(CASE WHEN review_score >= 4 THEN 1.0 ELSE 0.0 END), 2) AS positive_review_pct
FROM classified_orders
GROUP BY delivery_status
ORDER BY avg_review_score DESC;


-- ---------------------------------------------------------------------
-- (d) ¿Cada cuánto vuelve a comprar un cliente?
--
-- Pregunta de negocio: medir la recurrencia real de la base de clientes
-- para dimensionar estrategias de retención.
-- Grano: una fila por cliente con más de una compra.
-- ---------------------------------------------------------------------
WITH purchases AS (
    SELECT
        customer_id,
        CAST(order_date AS DATE) AS purchase_date
    FROM orders
    WHERE order_date IS NOT NULL
    GROUP BY customer_id, CAST(order_date AS DATE)
),
with_previous_purchase AS (
    SELECT
        customer_id,
        purchase_date,
        LAG(purchase_date) OVER (
            PARTITION BY customer_id
            ORDER BY purchase_date
        ) AS previous_purchase_date
    FROM purchases
),
purchase_intervals AS (
    SELECT
        customer_id,
        purchase_date,
        CAST(purchase_date - previous_purchase_date AS INTEGER) AS days_since_previous
    FROM with_previous_purchase
    WHERE previous_purchase_date IS NOT NULL
),
per_customer AS (
    SELECT
        customer_id,
        COUNT(*) AS repeat_purchases,
        AVG(days_since_previous) AS avg_days_between_purchases
    FROM purchase_intervals
    GROUP BY customer_id
)
SELECT
    COUNT(*) AS repeat_customers,
    SUM(repeat_purchases) AS repeat_purchases,
    ROUND(AVG(avg_days_between_purchases), 1) AS avg_days_between_purchases,
    ROUND(MIN(avg_days_between_purchases), 1) AS fastest_customer_avg_days,
    ROUND(MAX(avg_days_between_purchases), 1) AS slowest_customer_avg_days
FROM per_customer;
