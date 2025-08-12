# Escuelas y Bibliotecas – Análisis de Datos Abiertos

Este trabajo práctico se realizó en el marco de la materia **Laboratorio de Datos** (Licenciatura en Ciencias de Datos, UBA) – 1er Cuatrimestre 2025.

---

## Descripción

El objetivo principal del proyecto fue analizar si existe una relación entre la cantidad de **establecimientos educativos** y **bibliotecas populares** en cada departamento de las provincias de la República Argentina, utilizando datos abiertos nacionales.

El trabajo se desarrolló en varias etapas:

1. **Procesamiento y limpieza de datos**  
   - Transformación y normalización de los datasets de:
     - Padrón de población (INDEC).
     - Establecimientos educativos.
     - Bibliotecas populares (CONABIP).
     - Provincias y niveles educativos.
   - Unificación de formatos, tratamiento de valores nulos y estandarización de identificadores.
   - Modelado relacional y verificación de formas normales.
   
2. **Consultas SQL**  
   - Resumen de población y cantidad de establecimientos educativos por nivel educativo.
   - Conteo de bibliotecas populares fundadas desde 1950.
   - Integración de datos poblacionales, educativos y culturales por departamento.
   - Identificación del dominio de correo más frecuente en bibliotecas populares.

3. **Visualizaciones**  
   - Gráfico de barras: bibliotecas populares por provincia.
   - Dispersión: establecimientos educativos vs población, diferenciando niveles.
   - Boxplot: distribución de establecimientos educativos por departamento en cada provincia.
   - Dispersión log-log: relación de establecimientos educativos y bibliotecas por mil habitantes.

---

## Tecnologías y Librerías

- **Lenguaje:** Python
- **Librerías:**
  - `pandas`
  - `duckdb`
  - `matplotlib`
  - `seaborn`
  - `re`

Instalación rápida:
```bash
pip install pandas duckdb matplotlib seaborn
```

---

## Ejecución

1. Descargar y ubicar en la carpeta `TablasOriginales/` los archivos originales:

   - `padron_poblacion.xlsx`
   - `codigos_prov_depto_censo2010.xls`
   - `bibliotecas-populares.csv`
   - `2022_padron_oficial_establecimientos_educativos.xlsx`

2. Abrir el archivo `Código.py` en VSCode, Spyder o JupyterLab.

3. Ejecutar sección por sección (`#%%`) para reproducir:

   - Limpieza y generación de datasets modelo (`TablasModelo/`).
   - Consultas SQL.
   - Visualizaciones.

4. El script genera:

   - Archivos CSV limpios y normalizados.
   - Resultados de consultas SQL en DataFrames.
   - Gráficos listos para análisis e interpretación.

---

## Estructura del repositorio

```plaintext
📂 TablasModelo/
   ├── Carpeta inicialmente vacía. Se completa automáticamente al ejecutar `Código.py` con los datasets procesados y normalizados, listos para análisis y consultas SQL.
📂 TablasOriginales/
   ├── Archivos de datos crudos.
📄 Código.py
   ├── Script principal: limpieza de datos, consultas SQL y generación de visualizaciones.
📄 Enunciado.pdf
   ├── Enunciado del trabajo práctico con la descripción y objetivo del proyecto.
📄 Informe.pdf
   ├── Informe del trabajo práctico con explicación detallada del proceso y resultados.
📄 README.md
   ├── Descripción general del proyecto, instrucciones de instalación, ejecución y resultados destacados.
```
