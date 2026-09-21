"""EDA paso 1: estructura basica de SiteGiniLevel.csv.

A diferencia del CSV de Velasco (sep=";", decimal=","), este dataset
viene de tDAR (EE.UU.) en formato CSV estandar: sep="," y decimal ".".
"""
import pandas as pd

RUTA = "data/raw/SiteGiniLevel.csv"

# index_col=0 porque la primera columna del CSV es un indice de fila
# sin nombre (viene de un data.frame de R exportado con row.names).
df = pd.read_csv(RUTA, index_col=0)

print("Filas x columnas:", df.shape)
print()

print("Tipos de dato por columna:")
print(df.dtypes)
print()

# Nulos por columna, solo las que tienen al menos uno (74 columnas
# completas no aportan nada al leerlas).
nulos = df.isna().sum()
nulos = nulos[nulos > 0].sort_values(ascending=False)
print(f"Columnas con nulos ({len(nulos)} de {df.shape[1]}):")
print(nulos)
