"""EDA paso 2: cobertura geografica de SiteGiniLevel.csv.

Cuenta sitios por region (Bigregion > Region > Subregion > Subarea) y
revisa puntualmente la representacion de Sudamerica / Andes del sur,
porque el proyecto GINI tiene a Pablo Cruz (CONICET, Andes del sur)
como coautor y queremos declarar honestamente cuanto pesa esa region
en la muestra antes de construir cualquier conclusion.
"""
import pandas as pd

RUTA = "data/raw/SiteGiniLevel.csv"
df = pd.read_csv(RUTA, index_col=0)

print("Sitios por Bigregion:")
print(df["Bigregion"].value_counts())
print()

print("Sitios por Region dentro de 'South America':")
sudamerica = df[df["Bigregion"] == "South America"]
print(sudamerica["Region"].value_counts())
print()

print("Sitios por Subregion/Subarea dentro de 'Southern Andes':")
andes_sur = sudamerica[sudamerica["Region"] == "Southern Andes"]
print(andes_sur[["Subregion", "Subarea"]].value_counts())
print()

print("Sitios sin coordenadas (Latitude o Longitude nulas):")
sin_coords = df[df["Latitude"].isna() | df["Longitude"].isna()]
print(sin_coords[["Site", "Bigregion", "Region", "Subarea"]])
