# E-commerce Analytics — Portfolio de Data Analyst & Business Intelligence

Dashboard ejecutivo y análisis SQL sobre **15.000 órdenes de e-commerce** (enero 2025 – octubre 2026).
El proyecto demuestra un flujo completo de analista: generación reproducible de datos, limpieza con
criterio estadístico, consultas analíticas con CTEs y window functions, y una capa de presentación
en Streamlit con visualizaciones Plotly.

---

## Resumen ejecutivo

El negocio facturó **$1.656.361** en el periodo analizado, con un ticket promedio de **$110,42** y
**15.000 órdenes limpias**. La categoría líder es **Ropa y Accesorios (24,2 % de los ingresos)**.

El hallazgo principal es logístico: **el 21,4 % de los pedidos llega en más de 6 días** y esos pedidos
tienen una reseña promedio de **1,60 / 5**, frente a **3,99 / 5** en los pedidos a tiempo. Ningún pedido
retrasado registra una reseña positiva (4-5 estrellas), mientras que en los pedidos a tiempo la tasa es
del **75,3 %**. Reducir la demora por debajo de 7 días es la palanca con mayor impacto directo sobre la
satisfacción y la reputación de la tienda.

## Hallazgos cuantitativos

| Métrica | Valor |
| --- | --- |
| Ingresos totales | $1.656.361 |
| Órdenes limpias | 15.000 |
| Ticket promedio | $110,42 |
| Precio mediano por orden | $94,32 |
| Reseña promedio | 3,48 / 5 |
| Reseñas positivas (4-5 ★) | 59,2 % |
| Clientes con recompra | 50,3 % (4.293 de 8.542) |
| Órdenes por cliente | 1,75 |
| Días promedio entre compras | 182 (mediana: 146) |

**Facturación por categoría**

| Categoría | Ingresos | Participación | Órdenes |
| --- | ---: | ---: | ---: |
| Ropa y Accesorios | $400.728 | 24,2 % | 3.572 |
| Electrónica | $347.155 | 21,0 % | 3.235 |
| Hogar y Cocina | $301.488 | 18,2 % | 2.674 |
| Deportes | $207.787 | 12,5 % | 1.895 |
| Belleza | $200.229 | 12,1 % | 1.828 |
| Libros | $198.974 | 12,0 % | 1.796 |

**Impacto de la logística en la satisfacción**

| Estado de entrega | Órdenes | Reseña promedio | Reseñas positivas |
| --- | ---: | ---: | ---: |
| A tiempo (≤ 6 días) | 11.794 (78,6 %) | 3,99 / 5 | 75,3 % |
| Retrasada (> 6 días) | 3.206 (21,4 %) | 1,60 / 5 | 0,0 % |

La brecha es de **2,39 estrellas** y **75,3 puntos porcentuales** de reseñas positivas.

**Otros hallazgos**

- **Tendencia estable con sesgo alcista:** promedio mensual de $75.289; el último mes (octubre 2026)
  facturó $80.645, un **+6,7 %** frente a septiembre. El pico histórico es mayo 2025 ($81.870).
- **Concentración geográfica:** Centro ($454.498) y Norte ($404.598) generan el **51,9 %** de los ingresos.
- **Medios de pago:** tarjeta de crédito 45,2 %, PayPal 24,8 %, transferencia 18,1 %, efectivo 11,9 %.
- **Recurrencia moderada:** la mitad de la base vuelve a comprar, con una frecuencia de compra de
  aproximadamente seis meses.

## Stack tecnológico

- **Python 3.12** + **Pandas 3.1** / **NumPy 2.5** para generación, limpieza y agregaciones.
- **SQL estándar (PostgreSQL / DuckDB)** para las consultas analíticas.
- **Plotly 7.1** para visualización interactiva.
- **Streamlit 1.67** para el dashboard.
- Dependencias fijadas en `requirements.txt`.

## Estructura del repositorio

```text
.
├── AGENTS.md                        # Reglas de ingeniería del repositorio
├── app.py                           # Dashboard Streamlit (capa de presentación)
├── requirements.txt                 # Dependencias exactas
├── data/
│   └── raw/
│       └── ecommerce_orders.csv     # Dataset sintético versionado (necesario en Streamlit Cloud)
├── sql/
│   └── analytics_queries.sql        # 4 consultas analíticas comentadas
├── src/
│   └── generate_data.py             # Generador reproducible (seed 42)
├── .streamlit/
│   └── config.toml                  # Tema oscuro coherente con Plotly
└── .opencode/skills/                # Estándares del proyecto para agentes
```

## Pipeline de limpieza

El dashboard aplica y contabiliza estas reglas en cada carga:

1. **Deduplicación explícita:** `drop_duplicates()` sobre las 15.050 filas crudas; se eliminan 50 duplicados.
2. **Imputación robusta:** los 120 precios nulos se rellenan con la **mediana por categoría**
   (`groupby('category')['price'].transform('median')`), nunca con la media, para no distorsionar
   el ticket promedio por outliers.
3. **Categóricas nulas:** las 80 regiones vacías se imputan como `'No Especificada'`, conservando las
   órdenes para los conteos de facturación.
4. **Feature engineering vectorizado:** `month`, `is_delayed` (`shipping_days > 6`) y
   `shipping_bucket` (1-3, 4-6, 7-9 y 10+ días).

Resultado: **15.000 filas limpias** (99,7 % del dataset crudo). El dashboard muestra esta cifra junto
al detalle de imputaciones para que la limpieza sea auditable.

## Consultas SQL

`sql/analytics_queries.sql` contiene cuatro consultas documentadas con la pregunta de negocio que
responden:

| Consulta | Técnica |
| --- | --- |
| (a) Participación de ingresos por categoría | CTE + `SUM() OVER ()` + `DENSE_RANK()` |
| (b) Top 3 clientes por región | `DENSE_RANK() OVER (PARTITION BY region ...)` |
| (c) Satisfacción a tiempo vs. retrasada | Agregación condicional |
| (d) Recurrencia y días entre compras | `LAG() OVER (PARTITION BY customer_id ...)` |

Las cuatro se muestran dentro de la app, en el desplegable **“Ver las consultas SQL del análisis”**,
para que cualquier revisor pueda leer el código sin abrir el repositorio.

## Cómo ejecutar

### 1. Clonar e instalar

```bash
git clone <url-del-repositorio>
cd ProyectoPy

python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Generar el dataset

```bash
python src/generate_data.py
```

El script usa `seed=42`, valida los conteos de suciedad inyectada y escribe
`data/raw/ecommerce_orders.csv` (15.050 filas). Ejecutarlo de nuevo produce exactamente el mismo archivo.

### 3. Lanzar el dashboard

```bash
streamlit run app.py
```

El CSV ya está versionado, así que el paso 2 es opcional si solo quieres
ver la app.

> Si `python` no está en el PATH, usa la ruta completa del intérprete o el launcher `py` de Windows
> (`py -m venv .venv`).

## Despliegue

El repositorio incluye `data/raw/ecommerce_orders.csv` a propósito: Streamlit Community Cloud no
dispone de una base de datos externa y el dashboard arranca sin pasos adicionales. El `.gitignore`
excluye `data/processed/` pero **no** los CSV de `data/raw/`.

## Limitaciones y supuestos

- El dataset es **sintético** y reproducible; las distribuciones (log-normal de precios, Poisson de
  días de envío) imitan un negocio real, pero no corresponden a una empresa concreta.
- La correlación entre retraso y reseña se inyecta de forma determinista para demostrar el análisis;
  en datos reales el efecto sería más ruidoso.
- Los importes se expresan en USD y sin costes de envío, impuestos ni devoluciones.
- Las métricas del dashboard se recalculan sobre los filtros activos; los deltas comparan el último
  mes disponible con el anterior dentro del periodo filtrado.
