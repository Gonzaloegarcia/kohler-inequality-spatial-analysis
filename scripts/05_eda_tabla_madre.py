"""EDA de la tabla madre: gini_database_all_records_20240721--1.csv.

Es la tabla de microdatos: una fila por CASA individual (house_id),
con sus atributos de sitio pegados (Bigregion...Subarea, Latitude,
Longitude, etc.) y los de la casa (RoofedArea, LivingArea, etc.).
De aca salen por agregacion todas las demas tablas (SiteGiniLevel,
SiteGiniStor, SiteGiniNeib...).

Ojo: 'wc -l' en bash conto 54232 lineas (54231 filas de datos), pero
el material suplementario dice 53466 filas para 'All records'. Antes
de asumir cual numero es el correcto, dejamos que pandas cuente las
filas reales -- 'wc -l' cuenta saltos de linea crudos y se puede
confundir si un campo de texto entre comillas (como las citas en
Ref1/Ref2) trae un salto de linea adentro.
"""
import pandas as pd

RUTA = "data/raw/gini_database_all_records_20240721--1.csv"
df = pd.read_csv(RUTA)

print("Filas x columnas (segun pandas):", df.shape)
print()

print("Sitios unicos (site_id) vs. casas (house_id):")
print("site_id unicos:", df["site_id"].nunique())
print("house_id unicos:", df["house_id"].nunique())
print("filas totales:", len(df))
print()

print("Casas por sitio -- distribucion:")
print(df.groupby("site_id")["house_id"].nunique().describe())
print()

print("Nulos en columnas de area/superficie de la casa:")
cols_area = [
    "RoofedArea", "LivingArea", "UnroofedArea",
    "StorageArea", "StorageVolume", "TotalAreaHouse",
]
print(df[cols_area].isna().sum())
print()

print("Nulos en coordenadas y en DistanceToCenter:")
print(df[["Latitude", "Longitude", "DistanceToCenter"]].isna().sum())
print()

print("Valores de 'Coder' mas frecuentes (quien codifico los datos):")
print(df["Coder"].value_counts().head(15))
