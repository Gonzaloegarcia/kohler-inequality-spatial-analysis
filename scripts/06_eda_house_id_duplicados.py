"""Investigar los 18 house_id duplicados en la tabla madre.

Objetivo: decidir si son (a) la misma casa repetida por error, (b)
casas distintas que colisionan de ID por venir de fuentes/Coder
distintos, o (c) remediciones legitimas (ej. dos fases temporales)
que deberian tratarse como filas separadas en cualquier PK que
definamos mas adelante para el esquema SQL.
"""
import pandas as pd

RUTA = "data/raw/gini_database_all_records_20240721--1.csv"
df = pd.read_csv(RUTA, low_memory=False)

dup_ids = df["house_id"][df["house_id"].duplicated(keep=False)]
ids_unicos = dup_ids.unique()
print(f"house_id duplicados (valores unicos): {len(ids_unicos)}")
print(f"filas involucradas: {len(dup_ids)}")
print()

cols_clave = [
    "house_id", "site_id", "Site", "SiteID", "source_file", "Coder",
    "HouseGroup", "HousePeriod", "HousePhase", "StructureID",
    "TotalAreaHouse", "RoofedArea", "LivingArea",
]
dup_rows = df[df["house_id"].isin(ids_unicos)].sort_values("house_id")
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)
print(dup_rows[cols_clave].to_string(index=False))
