---
name: sql-analytics
description: Redacción de consultas SQL analíticas de nivel semi-senior usando CTEs y Window Functions.
---
# Estándares de SQL Analítico
1. Escribe SQL estándar (compatible con PostgreSQL / DuckDB / SQLite).
2. Estructura consultas complejas utilizando **CTEs (`WITH ... AS`)** en lugar de subconsultas anidadas difíciles de leer.
3. Incluye obligatoriamente **Window Functions** (`SUM() OVER ()`, `DENSE_RANK() OVER (PARTITION BY ... ORDER BY ...)` o `LAG()`) para cálculos de participación porcentual (*Share of Revenue*) y rankings segmentados.
4. Documenta cada consulta con un comentario superior explicando la pregunta de negocio que responde.
