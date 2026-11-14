---
name: clean-code-git
description: Estándares básicos de arquitectura de carpetas, manejo de dependencias y control de versiones.
---
# Reglas de Ingeniería y Estructura
1. Mantén una separación estricta de responsabilidades:
   - `data/raw/` para datos crudos.
   - `src/` para scripts de generación o procesamiento ETL.
   - `sql/` para consultas analíticas puras.
   - `app.py` en la raíz únicamente para la capa de presentación/dashboard.
2. Genera siempre un archivo `requirements.txt` exacto con las librerías utilizadas, sin dependencias innecesarias.
3. Crea un `.gitignore` adecuado para Python (ignorando `__pycache__/`, `.venv/`, `.DS_Store`, `.ipynb_checkpoints/`), pero **asegurándote de NO ignorar `data/raw/*.csv`** para que el despliegue en la nube funcione sin base de datos externa.
4. Usa rutas relativas (`pathlib` o `os.path`) para garantizar portabilidad entre Windows, Linux y Streamlit Cloud.
