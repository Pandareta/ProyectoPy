---
name: streamlit-bi-ui
description: Diseño de dashboards ejecutivos en Streamlit y visualizaciones interactivas con Plotly.
---
# Estándares de Visualización y BI
1. Configura la página con `st.set_page_config(..., layout="wide")`.
2. Usa `@st.cache_data` en las funciones de carga y limpieza para optimizar el rendimiento.
3. Estructura el layout en jerarquía visual de BI:
   - Barra lateral (`st.sidebar`) con filtros dinámicos (`multiselect`) de Región y Categoría.
   - Fila superior con 4 tarjetas de KPIs (`st.metric`) formateadas correctamente (moneda `$`, porcentajes `%` y deltas contextuales).
   - Grilla de 2x2 gráficos interactivos en Plotly con `template="plotly_dark"` y etiquetas claras en español.
4. Usa escalas de color semánticas (`RdYlGn`) cuando muestres satisfacción o rendimiento donde alto es positivo y bajo es crítico.
