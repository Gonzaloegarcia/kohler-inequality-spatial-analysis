"""EDA paso 5: estructura de SiteGiniNeib.csv (desigualdad intra-sitio).

Objetivo: confirmar con los datos reales el hallazgo que describe el
material suplementario -- que en general los barrios (HouseGroup) son
menos desiguales que el sitio completo -- antes de repetirlo como dato
propio en cualquier lado.
"""
import pandas as pd

RUTA = "data/raw/SiteGiniNeib.csv"
df = pd.read_csv(RUTA, index_col=0)

print("Filas x columnas:", df.shape)
print()

print("Sitios distintos (site_id) vs. filas totales:")
print("site_id unicos:", df["site_id"].nunique(), "| filas:", len(df))
print()

# HouseGroup por sitio: si un sitio tiene varias filas es porque se
# subdividio en varios barrios, no porque este duplicado.
barrios_por_sitio = df.groupby("site_id")["HouseGroup"].nunique()
print("Barrios (HouseGroup) por sitio -- distribucion:")
print(barrios_por_sitio.describe())
print()

# Gini_Diff = Gini_Site - GiniNeib (segun nuestra hipotesis de la
# sesion anterior). Si es mayoritariamente positivo, confirma que el
# sitio completo es MAS desigual que sus barrios por separado.
print("Gini_Diff (Gini_Site - GiniNeib): signo")
print((df["Gini_Diff"] > 0).value_counts(normalize=True))
print()
print("Gini_Diff: estadisticos")
print(df["Gini_Diff"].describe())
print()

print("Nulos en columnas clave (Latitude/Longitude, para saber si se")
print("puede cruzar con coordenadas de SiteGiniLevel):")
print(df[["Latitude", "Longitude"]].isna().sum())
