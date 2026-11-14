---
name: data-cleaning-etl
description: Buenas prácticas de limpieza de datos, imputación estadística y feature engineering con Pandas y NumPy.
---
# Estándares de ETL y Calidad de Datos
1. **Deduplicación:** Verifica y elimina registros duplicados explícitamente (`drop_duplicates()`) registrando cuántos se eliminaron.
2. **Imputación con criterio estadístico:** Nunca imputes variables numéricas sesgadas (como precios o ingresos) con la media (`mean`). Utiliza siempre la **mediana agrupada por categoría** (`groupby('category')['price'].transform('median')`) para evitar distorsiones por outliers.
3. **Valores categóricos nulos:** Impútalos como `'No Especificada'` en lugar de eliminar filas valiosas para el conteo de órdenes.
4. **Feature Engineering:** Deriva variables temporales (`year_month`) y banderas de reglas de negocio (`is_delayed` cuando `shipping_days > 6`) de forma vectorizada en Pandas.
