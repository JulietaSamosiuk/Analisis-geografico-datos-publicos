'''

TRABAJO PRÁCTICO 1 LABORATORIO DE DATOS
POBLACION, ESTABLECIMIENTOS EDUCATIVOS y BIBLIOTECAS POPULARES

1er CUATRIMESTRE 2025

NOMBRE DE GRUPO: Datos de Labo

INTEGRANTES DEL GRUPO:
 - Denisse Britez
 - Julieta Samosiuk
 - Lautaro Alvarez Bertoya


Este archivo se encuentra ordenado por:
    - Métodos auxiliares que utilizamos para la limpieza de datos
    - Limpieza y normalización de Datasets:
        - Padrón_Población
        - Provincias
        - Bibliotecas_Populares
        - Establecimientos_Educativos
        - Niveles_Educativos
        - Relacion_EE_Nivel
    - Consultas SQL. Por ejercicio desarrollamos:
        - Planteo del Ejercicio
        - Desarrollo de la Consulta SQL
        - Explicación de la Consulta SQL
    - Visualización. Por ejercicio desarrollamos:
        - Planteo del Ejercicio
        - Desarrollo del script
        - Impresión de Visualizaciones


'''

import pandas as pd
import re
import duckdb
import matplotlib.pyplot as plt
import seaborn as sns

# ------------------------------------------------------------------------- Métodos Auxiliares -------------------------------------------------------------------------

def limpiar_texto(texto):
    if pd.isna(texto):
        return texto
    return ' '.join(str(texto).strip().title().split())

def limpiar_mails_validos(mail):
    res = '-'
    if pd.isna(mail):
        return res

    # Convertimos a string y minúsculas
    mail_str = str(mail).lower()

    # Queremos borrar el caso (unico caso) en el que hay un mail repetido encerrado en < >
    mail_str = re.sub(r'<.*', '', mail_str)

    # Patrón básico para detectar mails válidos
    patron_mail = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'

    if re.match(patron_mail, mail_str):
        res = mail_str
    return res

def limpiar_cod_departamento(codigo:int):
    return codigo % 1000

def limpiar_cod_localidad_a_departamento(codigo:int):
  return codigo // 1000

def extraer_provincia_departamento(codigo: int) -> tuple[int, int]:
    provincia = codigo // 1_000
    departamento = codigo % 1_000
    return provincia, departamento


# ------------------------------------------------------------- Cargamos el archivo de "Padrón Población" -------------------------------------------------------------

file_path_padron = "TablasOriginales/padron_poblacion.xlsx"
df_padron = pd.read_excel(file_path_padron, skiprows = 10)

# Eliminamos filas completamente vacías.
df_padron.dropna(how = 'all', inplace = True)
df_padron.reset_index(drop = True, inplace = True)

# Queremos comenzar a generar el dataset limpio, iterando las filas desde que arranque una tabla de un departamento
# hasta que termine dicha tabla, y agrupar todo dentro de un unico dataset ordenado
data_limpia = []
codigo_area_actual = None
encabezado_detectado = False

for i, row in df_padron.iterrows():
    valores = row.tolist()
    if isinstance(valores[1], str) and "RESUMEN" in valores[1]:
      break
    # Buscamos filas que contengan "AREA # <codigo>".
    if isinstance(valores[1], str) and "AREA #" in valores[1]:
        #\s* — cualquier cantidad de espacios
        #(\d+) — uno o más dígitos → el código de área
        match = re.search(r"AREA #\s*(\d+)", valores[1])
        if match:
            codigo_area_actual = match.group(1)
            localidad_actual = str(valores[2]).strip() if pd.notna(valores[2]) else None
        encabezado_detectado = False # Reiniciamos encabezado para la próxima tabla.

    # Detectamos encabezado.
    elif not encabezado_detectado and isinstance(valores[1], str) and "Edad" in valores[1]:
        encabezado = valores[1:] # Ignoramos la columna 0 ("Frecuencia de Edad" que no sirve).
        encabezado_detectado = True

    # Si estamos dentro de una tabla de datos válida.
    elif encabezado_detectado and pd.notna(valores[1]):
        if str(valores[1]).strip().lower() != "total":
            fila_datos = dict(zip(encabezado, valores[1:])) # Mapeamos columnas.
            fila_datos['Codigo_area'] = codigo_area_actual
            fila_datos['Departamento'] = localidad_actual
            data_limpia.append(fila_datos)


df_padron_filtrado = pd.DataFrame(data_limpia)

# Limpiamos tipos de datos.
df_padron_filtrado = df_padron_filtrado.rename(columns={'Codigo_area': 'id_Departamento'})
df_padron_filtrado = df_padron_filtrado.rename(columns={'Casos': 'Habitantes'})
df_padron_filtrado['Habitantes'] = pd.to_numeric(df_padron_filtrado['Habitantes'], errors = 'coerce')
df_padron_filtrado['id_Departamento'] = pd.to_numeric(df_padron_filtrado['id_Departamento'], errors = 'coerce')


# Tenemos que limpiar los datos de CABA porque las comunas no concordaban entre los datasets
data_caba = {}
filas_caba = []
indices_a_eliminar = []
for i, row in df_padron_filtrado.iterrows():
  if 2000 <= row["id_Departamento"] < 3000:
    edad_row = row["Edad"]
    casos = row["Habitantes"]
    if edad_row in data_caba:
        data_caba[edad_row] += casos
    else:
        data_caba[edad_row] = casos
    indices_a_eliminar.append(i)

df_caba = pd.DataFrame([
    {
        "Edad": edad,
        "Habitantes": casos,
        "id_Departamento": 2000,
        "Departamento": "Ciudad Autónoma de Buenos Aires"
    }
    for edad, casos in data_caba.items()
])


df_padron_filtrado.drop(index=indices_a_eliminar, inplace=True)
df_padron_filtrado.reset_index(drop=True, inplace=True)
df_padron_filtrado = pd.concat([df_caba, df_padron_filtrado], ignore_index=True)
df_padron_filtrado[['id_Provincia', 'id_Departamento']] = pd.DataFrame(
    df_padron_filtrado['id_Departamento'].apply(extraer_provincia_departamento).tolist()
)

cols_padron_limpio = ['id_Provincia','id_Departamento', 'Departamento'] + [col for col in df_padron_filtrado.columns if col not in ['id_Provincia','id_Departamento', 'Departamento', '%', 'Acumulado %']]
df_padron_filtrado = df_padron_filtrado[cols_padron_limpio]



#Importamos el archivo con los datos de las Provincias y lo limpiamos y ordenamos
file_path_provincias = "TablasOriginales/codigos_prov_depto_censo2010.xls"
df_provincias = pd.read_excel(file_path_provincias,'Provincias', skiprows = 2, nrows=24) #Provincias se llama la hoja

df_provincias = df_provincias[['Código','Provincia']]
df_provincias['Código'] = df_provincias['Código'].astype(int)


# Guardar como CSV limpio
df_provincias.to_csv("TablasModelo/provincias.csv", index = False)
df_padron_filtrado.to_csv("TablasModelo/padron_poblacion_unificado.csv", index = False)


# --------------------------------------------------------- Cargamos el archivo de "Bibliotecas Populares" ------------------------------------------------------------
df_bibliotecas = pd.read_csv("TablasOriginales/bibliotecas-populares.csv")


"""Para realizar las consultas y el modelado de las Bases de Datos, debemos primero hacer un análisis de las bases para limpiar los datos y columnas para trabajar de forma mas cómoda y prolija.
Primero recorremos las columnas de cáda tabla para ver qué informacion nos importa, y que información podemos descartar.

Arrancando por la base de Padrón Poblacion, detectamos que la tabla tenía un formato muy incomodo con el cuál trabajar. Era una tabla llena de tablas que agrupaban habitantes según el departamento en el que se encontraban. Por cada departamento había una tabla. Entonces decidimos organizarlo en una única tabla que tenga los identificadores de departamento y toda su información correspondiente. Decidimos rescatar las columnas:
* id_departamento
* departamento
* edad
* habiantes

Para Establecimientos Educativos, ademas de analizar las columnas y limpiar los datos, tuvimos que hacer una agrupación de información sobre

Decidimos rescatar las columnas:


Para Bibliotecas Populares, decidimos rescatar las columnas:
* id_BP
* id_provincia
* id_departamento
* nombre
* mail
* fecha_fundacion
"""

columnas_a_eliminar = [
    'provincia', 'departamento', 'observacion', 'categoria', 'subcategoria', 'domicilio','localidad', 'piso', 'cp', 'web', 'cod_tel', 'telefono','informacion_adicional', 'latitud', 'longitud', 'tipo_latitud_longitud', 'fuente', 'anio_actualizacion'
]
df_bibliotecas_filtrado = df_bibliotecas.drop(columns = [col for col in columnas_a_eliminar if col in df_bibliotecas.columns])
df_bibliotecas_filtrado = df_bibliotecas_filtrado.rename(columns={'nro_conabip': 'id_BP'})
cols = ['id_BP']+[col for col in df_bibliotecas_filtrado.columns if col not in ['id_BP']]
df_bibliotecas_filtrado = df_bibliotecas_filtrado[cols]

df_bibliotecas_filtrado['mail'] = df_bibliotecas_filtrado['mail'].apply(limpiar_mails_validos)

# Unificamos el código de Departamento para que quede igual en todos los Datasets
df_bibliotecas_filtrado['id_departamento'] = df_bibliotecas_filtrado['id_departamento'].apply(limpiar_cod_departamento)
cols = [col for col in df_bibliotecas_filtrado.columns if col not in ['cod_localidad']]
df_bibliotecas_filtrado = df_bibliotecas_filtrado[cols]

df_bibliotecas_filtrado['nombre'] = df_bibliotecas_filtrado['nombre'].apply(limpiar_texto)

df_bibliotecas_filtrado.to_csv("TablasModelo/bibliotecas_populares_CONABIP_2023_limpio.csv", index = False)



# ------------------------------------------------------ Cargamos el archivo de "Establecimientos Educativos" ---------------------------------------------------------

# Método para unificar niveles educativos en una columna
def unificar_niveles_colegios(fila):
    niveles = []
    if fila['Nivel inicial - Jardín maternal'] == 1 or fila['Nivel inicial - Jardín de infantes'] == 1:
        niveles.append('Jardín')
    if fila['Primario'] == 1:
        niveles.append('Primario')
    if fila['Secundario'] == 1:
        niveles.append('Secundario')
    return ', '.join(niveles) if niveles else '-'

# Método para normalizar los codigos de departamento de CABA
def normalizacion_CABA(codigo: int) -> int:
    return 2000 if codigo < 3000 else codigo

df_establecimientos = pd.read_excel("TablasOriginales/2022_padron_oficial_establecimientos_educativos.xlsx", header = 6)

# Filtramos solo las columnas necesarias para procesar.
columnas_utiles = [
    'Cueanexo', 'Nombre', 'Código de localidad',
]

#Columnas de niveles educativos
columnas_nivel_colegio = df_establecimientos.columns[20:24].tolist()

nombre_columnas = columnas_utiles+columnas_nivel_colegio
df_establecimientos_filtrado = df_establecimientos[nombre_columnas]


df_establecimientos_filtrado = df_establecimientos[nombre_columnas].copy()

# Creamos la columna de Nivel educativo y le aplicamos la funcion de unificar
df_establecimientos_filtrado['Nivel Educativo'] = df_establecimientos_filtrado.apply(unificar_niveles_colegios, axis=1)

# Borramos las columnas extra que nos sobraron por unificar las columnas
df_establecimientos_filtrado = df_establecimientos_filtrado.drop(columns = ['Nivel inicial - Jardín maternal', 'Nivel inicial - Jardín de infantes', 'Primario','Secundario'])

df_establecimientos_filtrado = df_establecimientos_filtrado.rename(columns={'Cueanexo':'id_EE'})
df_establecimientos_filtrado = df_establecimientos_filtrado.rename(columns={'Código de localidad':'id_Departamento'})

# Unificamos el código de Departamento para que quede igual en todos los Datasets
df_establecimientos_filtrado['id_Departamento'] = df_establecimientos_filtrado['id_Departamento'].apply(limpiar_cod_localidad_a_departamento)
df_establecimientos_filtrado[['id_Provincia', 'id_Departamento']] = pd.DataFrame(
    df_establecimientos_filtrado['id_Departamento'].apply(normalizacion_CABA).apply(extraer_provincia_departamento).tolist()
)
df_establecimientos_filtrado['Nombre'] = df_establecimientos_filtrado['Nombre'].apply(limpiar_texto)

niveles_Educativos = [
    {
        'id_Nivel_Educativo': 1,
        'nombre': 'Jardín',
        'desde_edad': 0,
        'hasta_edad': 5
    },
    {
        'id_Nivel_Educativo': 2,
        'nombre': 'Primario',
        'desde_edad': 6,
        'hasta_edad': 12
    },
    {
        'id_Nivel_Educativo': 3,
        'nombre': 'Secundario',
        'desde_edad': 13,
        'hasta_edad': 18
    }
]

df_niveles = pd.DataFrame(niveles_Educativos)
df_niveles.to_csv("TablasModelo/niveles_educativos.csv", index = False)

#Quiero hacer la tabla que tenga la relación de id_EE con id_Nivel_Educativo
df_relacion_EE_nivel = df_establecimientos_filtrado[["id_EE","Nivel Educativo"]].copy()
df_relacion_EE_nivel['Nivel Educativo'] = df_relacion_EE_nivel['Nivel Educativo'].str.split(', ')
df_relacion_EE_nivel = df_relacion_EE_nivel.explode('Nivel Educativo')
df_relacion_EE_nivel = df_relacion_EE_nivel.rename(columns={'Nivel Educativo':'nombre'})

#Hago merge para traerme los datos de la tabla de niveles, y luego borro el nombre del nivel educativo
df_relacion_EE_nivel = df_relacion_EE_nivel.merge(df_niveles[['id_Nivel_Educativo', 'nombre']], on='nombre', how='left')
df_relacion_EE_nivel['id_Nivel_Educativo'] = pd.to_numeric(
    df_relacion_EE_nivel['id_Nivel_Educativo'], errors='coerce'
).astype('Int64')

df_relacion_EE_nivel = df_relacion_EE_nivel[['id_EE','id_Nivel_Educativo']]
#Borro la columna de Nivel Educativo porque ahora esa info se encuentra en la tabla de relación
df_establecimientos_filtrado = df_establecimientos_filtrado[[col for col in df_establecimientos_filtrado.columns if col not in ['Nivel Educativo']]]

df_relacion_EE_nivel.to_csv("TablasModelo/relacion_EE_nivel.csv", index = False)

df_establecimientos_filtrado.to_csv("TablasModelo/establecimientos_educativos_filtrado.csv", index = False)


# ------------------------------------------------------------------------- Consultas SQL -------------------------------------------------------------------------

#Declaramos variables globales leyendo los archivos generados anteriormente
bibliotecas = pd.read_csv("TablasModelo/bibliotecas_populares_CONABIP_2023_limpio.csv")
niveles = pd.read_csv("TablasModelo/niveles_educativos.csv")
establecimientos = pd.read_csv("TablasModelo/establecimientos_educativos_filtrado.csv")
poblacion = pd.read_csv("TablasModelo/padron_poblacion_unificado.csv")
provincias = pd.read_csv("TablasModelo/provincias.csv")
relacion_EE_nivel = pd.read_csv("TablasModelo/relacion_EE_nivel.csv")

con = duckdb.connect()

con.register('ee', establecimientos)
con.register('ee_nivel', relacion_EE_nivel)
con.register('niveles', niveles)
con.register('poblacion', poblacion)
con.register('provincias', provincias)

### Consulta 1:
"""
Queremos construir una tabla resumen que, por cada departamento, nos diga:

- La provincia y el nombre del departamento.

- Cuántos establecimientos educativos hay de cada nivel (Jardín, Primaria, Secundaria).

- Cuántos habitantes hay en el rango de edad correspondiente a cada nivel.

Luego ordenamos el resultado alfabéticamente por provincia y, dentro de cada provincia, de mayor a menor según cantidad de escuelas primarias.

"""

consulta_1 = """
-- Subconsulta: población por provincia, departamento y nivel
WITH poblacion_por_nivel AS (
    SELECT
        p.id_Provincia,
        p.id_Departamento,
        SUM(CASE WHEN n.nombre = 'Jardín' AND p.Edad BETWEEN n.desde_edad AND n.hasta_edad THEN p.Habitantes ELSE 0 END) AS Poblacion_Jardin,
        SUM(CASE WHEN n.nombre = 'Primario' AND p.Edad BETWEEN n.desde_edad AND n.hasta_edad THEN p.Habitantes ELSE 0 END) AS Poblacion_Primaria,
        SUM(CASE WHEN n.nombre = 'Secundario' AND p.Edad BETWEEN n.desde_edad AND n.hasta_edad THEN p.Habitantes ELSE 0 END) AS Poblacion_Secundaria,
        MAX(p.Departamento) AS Departamento  -- obtenemos el nombre del departamento
    FROM poblacion p
    CROSS JOIN niveles n
    GROUP BY p.id_Provincia, p.id_Departamento
),

-- Subconsulta: cantidad de EE por provincia, departamento y nivel
establecimientos_por_nivel AS (
    SELECT
        e.id_Provincia,
        e.id_Departamento,
        SUM(CASE WHEN n.nombre = 'Jardín' THEN 1 ELSE 0 END) AS Jardines,
        SUM(CASE WHEN n.nombre = 'Primario' THEN 1 ELSE 0 END) AS Primarias,
        SUM(CASE WHEN n.nombre = 'Secundario' THEN 1 ELSE 0 END) AS Secundarios
    FROM ee e
    JOIN ee_nivel en ON e.id_EE = en.id_EE
    JOIN niveles n ON en.id_Nivel_Educativo = n.id_Nivel_Educativo
    GROUP BY e.id_Provincia, e.id_Departamento
)

-- Unión de ambas subconsultas
SELECT
    prov.Provincia,
    pop.Departamento,
    est.Jardines,
    pop.Poblacion_Jardin,
    est.Primarias,
    pop.Poblacion_Primaria,
    est.Secundarios,
    pop.Poblacion_Secundaria
FROM establecimientos_por_nivel est
JOIN poblacion_por_nivel pop
    ON est.id_Provincia = pop.id_Provincia AND est.id_Departamento = pop.id_Departamento
JOIN provincias prov
    ON est.id_Provincia = prov.Código
ORDER BY prov.Provincia ASC, est.Primarias DESC
"""

resultado_consulta_1 = con.execute(consulta_1).df()

resultado_consulta_1.head()

"""

1. Subconsulta poblacion_por_nivel
- Agrupa la población por nivel educativo.

2. Subconsulta establecimientos_por_nivel
- Cuenta escuelas por nivel educativo.

3. Consulta principal
- Une esas dos subconsultas con la tabla de provincias y da el resultado final.
"""

### Consulta 2:
consulta_2 = """
SELECT
    prov.Provincia,
    MAX(pob.Departamento) AS Departamento,  -- Obtenemos el nombre del departamento
    COUNT(*) AS "Cantidad de BP fundadas desde 1950"
FROM bibliotecas b
JOIN provincias prov ON b.id_provincia = prov.Código
LEFT JOIN poblacion pob
    ON b.id_provincia = pob.id_Provincia AND b.id_departamento = pob.id_Departamento
WHERE CAST(b.fecha_fundacion AS DATE) >= DATE '1950-01-01'
GROUP BY prov.Provincia, b.id_provincia, b.id_departamento
ORDER BY prov.Provincia ASC, "Cantidad de BP fundadas desde 1950" DESC
"""


resultado_consulta_2 = con.execute(consulta_2).df()

resultado_consulta_2.head()

"""
1. FROM bibliotecas b

- Tomamos como tabla base a bibliotecas, ya que es donde están las fechas de fundación.

2. JOIN provincias prov ON b.id_provincia = prov.Código

- Usamos un JOIN para unir con la tabla provincias, y así obtener el nombre de la provincia correspondiente a cada biblioteca.

- Usamos JOIN porque todas las bibliotecas tienen una provincia válida, así que no se pierde información al hacerlo.

3. LEFT JOIN poblacion pob ...

- Hacemos un LEFT JOIN con la tabla padron_poblacion_unificado para conseguir el nombre del departamento.

- Usamos LEFT JOIN porque puede que no exista una entrada en poblacion para algunos departamentos, pero igualmente queremos conservar esas bibliotecas. Si usáramos JOIN, se eliminarían.

4. WHERE CAST(b.fecha_fundacion AS DATE) >= DATE '1950-01-01'

- Filtramos para quedarnos solo con bibliotecas fundadas desde 1950.

- Hacemos un CAST porque fecha_fundacion viene como texto (VARCHAR), y queremos compararlo como una fecha real (DATE). Esto evita errores y asegura una comparación válida.

5. GROUP BY ...

- Agrupamos por provincia y por departamento para poder contar cuántas bibliotecas hay por cada uno.

6. MAX(pob.Departamento) AS Departamento

- Como el nombre del departamento está repetido en cada fila con el mismo valor, podemos usar MAX() para obtenerlo de forma segura. (También podríamos usar MIN() o un FIRST_VALUE()).

7. COUNT(*) AS "Cantidad de BP fundadas desde 1950"

- Contamos la cantidad de bibliotecas por grupo.

8. ORDER BY ...

- Ordenamos por provincia alfabéticamente y dentro de cada provincia, de mayor a menor cantidad de BP fundadas desde 1950.
"""

### Consulta 3:
"""
### Consulta 3:

Necesitamos combinar datos de las siguientes tablas:

- provincias: para obtener el nombre de la provincia.

- poblacion: para saber la población total por departamento.

- establecimientos: para contar establecimientos educativos (modalidad común).

- bibliotecas: para contar bibliotecas populares.

Como queremos incluir todos los departamentos, incluso aquellos sin EE o BP, haremos una unión completa de las fuentes de datos relevantes, usando LEFT JOIN desde población como base (ya que tiene todos los departamentos).
"""

consulta_3 = """
-- Subconsulta: población total por departamento
WITH poblacion_total AS (
    SELECT
        id_Provincia,
        id_Departamento,
        MAX(Departamento) AS Departamento,
        SUM(Habitantes) AS Poblacion
    FROM poblacion
    GROUP BY id_Provincia, id_Departamento
)

SELECT
    prov.Provincia,
    pop.Departamento,
    COUNT(DISTINCT ee.id_EE) AS Cant_EE,
    COUNT(DISTINCT b.id_BP) AS Cant_BP,
    pop.Poblacion
FROM poblacion_total pop
LEFT JOIN provincias prov
    ON pop.id_Provincia = prov.Código
LEFT JOIN establecimientos ee
    ON pop.id_Provincia = ee.id_Provincia AND pop.id_Departamento = ee.id_Departamento
LEFT JOIN bibliotecas b
    ON pop.id_Provincia = b.id_provincia AND pop.id_Departamento = b.id_departamento
GROUP BY prov.Provincia, pop.Departamento, pop.Poblacion
ORDER BY Cant_EE DESC, Cant_BP DESC, prov.Provincia ASC, pop.Departamento ASC;
"""

resultado_consulta_3 = con.execute(consulta_3).df()

resultado_consulta_3.head()

"""
1. Primera Subconsulta: Cálculo de la Población Total por Departamento

- Calcula la población total por departamento sumando los habitantes para cada combinación de id_Provincia y id_Departamento.

- Utiliza MAX(Departamento) para obtener el nombre del departamento. Aunque este campo puede repetirse varias veces por los diferentes rangos de edad, el uso de MAX() asegura que solo se muestre un valor por departamento.

- El resultado de esta subconsulta es una tabla con la población total de cada departamento, junto con el nombre del departamento (con la función MAX) y los identificadores correspondientes a provincia y departamento.

2. Selección Final de Datos y Cálculos

- Selecciona la provincia, departamento, y realiza las siguientes agregaciones:

  - Cant_EE: La cantidad de establecimientos educativos (EE), contando los distintos id_EE de la tabla establecimientos.

  - Cant_BP: La cantidad de bibliotecas populares (BP), contando los distintos id_BP de la tabla bibliotecas.

  - Poblacion: La población total de cada departamento, obtenida de la subconsulta poblacion_total.

3. Joins con Otras Tablas

- Se realiza un LEFT JOIN entre la subconsulta poblacion_total y la tabla provincias para obtener el nombre de la provincia mediante el código de la provincia (id_Provincia).

- Se realiza un LEFT JOIN entre poblacion_total y la tabla establecimientos para obtener los datos de los establecimientos educativos (si existen).

- Se realiza un LEFT JOIN entre poblacion_total y la tabla bibliotecas para obtener los datos de las bibliotecas populares (si existen).

- Por qué usar LEFT JOIN: Esto asegura que, incluso si un departamento no tiene establecimientos educativos o bibliotecas, aún aparecerá en el reporte con las cifras correspondientes a cero para esos campos.
"""

### Consulta 4:
"""
El objetivo es obtener, por cada departamento, la provincia, el nombre del departamento y el dominio de correo electrónico más frecuente entre las Bibliotecas Populares (BP).
"""

consulta_4 = """
-- Subconsulta: contabilizamos dominios conocidos por provincia y departamento
WITH dominios_contados AS (
    SELECT
        b.id_provincia,
        b.id_departamento,
        CASE
            WHEN split_part(b.mail, '@', 2) IS NULL THEN 'Desconocido'
            ELSE split_part(split_part(b.mail, '@', 2), '.', 1)
        END AS dominio,
        COUNT(*) AS cantidad
    FROM bibliotecas b
    WHERE b.mail IS NOT NULL AND b.mail LIKE '%@_%'
    GROUP BY b.id_provincia, b.id_departamento, dominio
),

-- Subconsulta: obtenemos el máximo uso de dominio por departamento
maximos AS (
    SELECT
        id_provincia,
        id_departamento,
        MAX(cantidad) AS max_cantidad
    FROM dominios_contados
    GROUP BY id_provincia, id_departamento
)

-- Consulta final: devolvemos el dominio más frecuente por departamento
SELECT
    prov.Provincia,
    MAX(pob.Departamento) AS Departamento,
    d.dominio AS "Dominio más frecuente en BP"
FROM dominios_contados d
JOIN maximos m
    ON d.id_provincia = m.id_provincia
    AND d.id_departamento = m.id_departamento
    AND d.cantidad = m.max_cantidad
JOIN provincias prov
    ON d.id_provincia = prov.Código
LEFT JOIN poblacion pob
    ON d.id_provincia = pob.id_Provincia
    AND d.id_departamento = pob.id_Departamento
GROUP BY prov.Provincia, d.dominio, d.id_provincia, d.id_departamento
ORDER BY prov.Provincia ASC, Departamento ASC;
"""

resultado_consulta_4 = con.execute(consulta_4).df()

resultado_consulta_4.head()

"""
1.  Primera subconsulta: dominios_contados

- Parte de la tabla bibliotecas.

- Elimina las filas donde el campo mail es nulo (b.mail IS NOT NULL).

- Usa CASE para clasificar los mails según el dominio conocido (por ahora: Gmail, Hotmail, Yahoo). Todo lo que no coincida con esos patrones va como "Otro".

- Agrupa por provincia, departamento y dominio, y cuenta cuántas bibliotecas hay con cada uno.

2. Segunda subconsulta: maximos

- Parte de la subconsulta anterior (dominios_contados).

- Para cada departamento:

  - Busca cuál es el dominio más usado (el que tiene la cantidad máxima de bibliotecas).

  - Guarda esa cantidad máxima por departamento.
  
3. Consulta final (principal)

- Parte de dominios_contados, pero filtra para quedarse solo con los dominios más usados (los que tienen la cantidad máxima en su departamento).

- Uniones:

  - JOIN maximos: para asegurarse de que solo quede el más frecuente.

  - JOIN provincias: para obtener el nombre de la provincia.

  - LEFT JOIN poblacion: para obtener el nombre del departamento.

- MAX(pob.Departamento):

  - En cada grupo, el nombre del departamento es el mismo, así que usamos MAX para poder seleccionarlo (esto es una forma segura de incluirlo en el SELECT sin meterlo en el GROUP BY completo).

- Agrupamiento:

  - Agrupa por provincia, dominio, id_provincia y id_departamento para poder aplicar agregaciones y garantizar que los datos están bien unidos.

- Ordenamiento:

  - Ordena alfabéticamente por nombre de provincia y luego por nombre de departamento.
"""

# ----------------------------------------------------------------------- Visualización -----------------------------------------------------------------------
# Declaramos variables globales leyendo los archivos generados anteriormente
# Para cada ejercicio, delante de las variables colocamos un "vN_" significando visualizacion numero N
bibliotecas = pd.read_csv("TablasModelo/bibliotecas_populares_CONABIP_2023_limpio.csv")
niveles = pd.read_csv("TablasModelo/niveles_educativos.csv")
establecimientos = pd.read_csv("TablasModelo/establecimientos_educativos_filtrado.csv")
padron = pd.read_csv("TablasModelo/padron_poblacion_unificado.csv")
provincias = pd.read_csv("TablasModelo/provincias.csv")
ee_nivel = pd.read_csv("TablasModelo/relacion_EE_nivel.csv")




"""### 1. Cantidad de bibliotecas populares por provincia, ordenadas de mayor a menor.

Para este gráfico necesitamos dos tablas:

- bibliotecas.

- provincias.

En este caso, consideramos más adecuado trabajar con un gráfico de barras.
"""
# Agrupamos cantidad de BP por provincia (por código).
v1_bp_por_provincia = bibliotecas.groupby("id_provincia").size().reset_index(name = "Cantidad_BP")

# Unimos con nombres de provincia.
v1_bp_por_provincia = v1_bp_por_provincia.merge(provincias, left_on = "id_provincia", right_on = "Código")

# Ordenamos de forma decreciente.
v1_bp_por_provincia = v1_bp_por_provincia.sort_values("Cantidad_BP", ascending = False)

# Graficamos.
plt.figure(figsize = (10, 6))
sns.barplot(data = v1_bp_por_provincia, x = "Provincia", y = "Cantidad_BP", hue = "Provincia", palette = "viridis", legend = False)
plt.xticks(rotation = 45, ha = "right")
plt.title("Cantidad de Bibliotecas Populares por Provincia")
plt.xlabel("Provincia")
plt.ylabel("Cantidad de BP")
plt.tight_layout()
plt.show()




"""### 2. Cantidad de establecimientos educativos por departamento en función de la población, diferenciando por nivel educativo y grupo etario.

Para este gráfico necesitamos cuatro tablas:
    
- establecimientos.

- padron_poblacion_unificado.

- niveles.

- relacion_EE_nivel.

En este caso, consideramos más adecuado trabajar con un gráfico de dispersión (scatter plot).
"""
# Unimos establecimientos con niveles educativos.
v2_establecimientos_copy = establecimientos.merge(ee_nivel, on = "id_EE", how = "inner")
v2_establecimientos_copy = v2_establecimientos_copy.merge(niveles, on = "id_Nivel_Educativo", how = "left")

# Renombramos para mayor claridad.
v2_establecimientos_copy = v2_establecimientos_copy.rename(columns = {"nombre": "Nivel Educativo"})

# Creamos columna "Grupo Etario".
v2_establecimientos_copy["Grupo Etario"] = v2_establecimientos_copy["desde_edad"].astype(str) + "-" + v2_establecimientos_copy["hasta_edad"].astype(str) + " años"

# Agrupamos cantidad de EE por departamento y nivel
v2_ee_por_departamento = v2_establecimientos_copy.groupby(["id_Provincia", "id_Departamento", "Nivel Educativo", "Grupo Etario"]).size().reset_index(name = "Cantidad_EE")

# Calculamos población total por departamento.
v2_poblacion_departamento = padron.groupby(["id_Provincia", "id_Departamento"])["Habitantes"].sum().reset_index(name = "Poblacion_total")

# Unimos con población.
v2_final = v2_ee_por_departamento.merge(v2_poblacion_departamento, on = ["id_Provincia", "id_Departamento"], how = "left")

# Graficamos.
plt.figure(figsize = (10, 6))
sns.scatterplot(
    data = v2_final,
    x = "Poblacion_total",
    y = "Cantidad_EE",
    hue = "Nivel Educativo",
    style = "Grupo Etario",
    s = 100,
    palette = "Set2"
)

plt.title("Cantidad de Establecimientos Educativos vs Población por Departamento")
plt.xlabel("Población Total del Departamento por Millon de Personas")
plt.ylabel("Cantidad de EE")
plt.grid(True)
plt.tight_layout()
plt.legend()
plt.show()




"""### 3. Distribución de establecimientos educativos por departamento en cada provincia.

Para este gráfico necesitamos dos tablas:

- establecimientos.

- provincias.

En este caso, utilizamos un boxplot por provincia, donde cada “caja” representa la distribución de EE entre sus departamentos.
"""
# Agrupamos cantidad de EE por departamento y provincia.
v3_ee_por_departamento = establecimientos.groupby(["id_Provincia", "id_Departamento"])['id_EE'].nunique().reset_index(name = "Cantidad_EE")

# Unimos con nombres de provincia.
v3_ee_por_departamento = v3_ee_por_departamento.merge(provincias, left_on = "id_Provincia", right_on = "Código")

# Ordenamos las provincias por la mediana de EE por departamento.
v3_orden_provincias = v3_ee_por_departamento.groupby("Provincia")["Cantidad_EE"].median().sort_values(ascending = False).index

# Graficamos.
plt.figure(figsize = (10, 6))
sns.boxplot(data = v3_ee_por_departamento, x = "Provincia", y = "Cantidad_EE", order = v3_orden_provincias)
plt.xticks(rotation = 45, ha = "right")
plt.xlabel("Provincia")
plt.ylabel("Cantidad de EE")
plt.title("Distribución de Establecimientos Educativos por Departamento en cada Provincia")
plt.tight_layout()
plt.show()




"""### 4. Relación entre la cantidad de bibliotecas populares cada mil habitantes y de establecimientos educativos cada mil habitantes por departamento.

Para este gráfico necesitamos tres tablas:

- establecimientos.

- bibliotecas.

- padron_poblacion_unificado.

En este caso, consideramos más adecuado trabajar con un gráfico de dispersión.
"""
# Agrupamos EE por provincia y departamento.
v4_ee_por_depto = establecimientos.groupby(['id_Provincia', 'id_Departamento'])['id_EE'].nunique().reset_index(name = 'cantidad_EE')

# Agrupamos BP por provincia y departamento.
v4_bp_por_depto = bibliotecas.groupby(['id_provincia', 'id_departamento']).size().reset_index(name = 'cantidad_BP')

# Calculamos población total por departamento.
v4_poblacion_total = padron.groupby(['id_Provincia', 'id_Departamento'])['Habitantes'].sum().reset_index(name = 'poblacion_total')

# Renombramos columnas para unir.
v4_bp_por_depto = v4_bp_por_depto.rename(columns = {'id_provincia': 'id_Provincia', 'id_departamento': 'id_Departamento'})

# Merge de las tres tablas.
v4_final = pd.merge(v4_ee_por_depto, v4_poblacion_total, on = ['id_Provincia', 'id_Departamento'], how = 'inner')
v4_final = pd.merge(v4_final, v4_bp_por_depto, on = ['id_Provincia', 'id_Departamento'], how = 'left')
v4_final['cantidad_BP'] = v4_final['cantidad_BP'].fillna(0)

# Calculamos indicadores por mil habitantes.
v4_final['EE_por_mil'] = v4_final['cantidad_EE'] / v4_final['poblacion_total'] * 1000
v4_final['BP_por_mil'] = v4_final['cantidad_BP'] / v4_final['poblacion_total'] * 1000

v4_final_log = v4_final[(v4_final['EE_por_mil'] > 0) & (v4_final['BP_por_mil'] > 0)]

# Graficamos.
plt.figure(figsize = (10, 6))
sns.scatterplot(data = v4_final_log, x = 'EE_por_mil', y = 'BP_por_mil', alpha = 0.6)

plt.xscale('log')
plt.yscale('log')

plt.xlabel("Establecimientos Educativos por mil habitantes (escala log)")
plt.ylabel("Bibliotecas Populares por mil habitantes (escala log)")
plt.title("Relación entre EE y BP cada mil habitantes por departamento")
plt.grid(True)
plt.tight_layout()
plt.show()

