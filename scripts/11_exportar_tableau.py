"""Exporta gini.sites/moran_by_region/homophily_by_site para Tableau.

El esquema SQL se mantiene en ingles (decision del 07/09/2026:
mantener el ingles del dataset original pero los dashboards de
Tableau en espanol). Este script es la frontera de traduccion:
nombres de columna Y valores de la region (porque van a aparecer
como etiquetas en los graficos, no solo como encabezados).

Nota sobre coordenadas: a diferencia de Velasco, no se aplica jitter
aca. El propio paper (Special Feature companion) declara que las
ubicaciones de sitios en paises sensibles a saqueo "will be obscured
(generalized)" antes de publicar el dataset -- la generalizacion, si
corresponde, ya la hicieron los autores originales en el CSV de tDAR.
"""
import os

import pandas as pd
import psycopg2

RUTA_SALIDA = "data/processed/tableau"

TRADUCCION_BIGREGION = {
    "Africa": "África",
    "Asia": "Asia",
    "Europe": "Europa",
    "Mesoamerica": "Mesoamérica",
    "North America": "Norteamérica",
    "Oceania": "Oceanía",
    "South America": "Sudamérica",
}


def conectar():
    return psycopg2.connect(
        dbname="kohler_gini", user="postgres",
        password=os.environ["PGPASSWORD"], host="localhost", port=5432,
    )


def consultar(conexion, consulta: str) -> pd.DataFrame:
    with conexion.cursor() as cursor:
        cursor.execute(consulta)
        filas = cursor.fetchall()
        columnas = [d.name for d in cursor.description]
    return pd.DataFrame(filas, columns=columnas)


def exportar_sitios(conexion) -> None:
    df = consultar(
        conexion,
        "SELECT site_id, site_name, bigregion, region, subarea, "
        "latitude, longitude, gini, count_hh FROM gini.sites",
    )
    df["bigregion"] = df["bigregion"].map(TRADUCCION_BIGREGION)
    df = df.rename(columns={
        "site_id": "sitio_id",
        "site_name": "nombre_sitio",
        "bigregion": "region_grande",
        "region": "region",
        "subarea": "subarea",
        "latitude": "latitud",
        "longitude": "longitud",
        "gini": "gini",
        "count_hh": "cantidad_casas",
    })
    df.to_csv(
        f"{RUTA_SALIDA}/sitios.csv", index=False, lineterminator="\n"
    )
    print(f"[sitios.csv] {len(df)} filas")


def exportar_moran_por_region(conexion) -> None:
    df = consultar(conexion, "SELECT * FROM gini.moran_by_region")
    df["bigregion"] = df["bigregion"].map(TRADUCCION_BIGREGION)
    df = df.rename(columns={
        "bigregion": "region_grande",
        "n_sitios": "cantidad_sitios",
        "moran_i": "moran_i",
        "p_valor": "p_valor",
        "z_score": "z_score",
        "n_componentes": "cantidad_componentes",
        "dist_vecino_mediana_km": "distancia_vecino_mediana_km",
        "dist_vecino_maxima_km": "distancia_vecino_maxima_km",
        "confiable": "confiable",
    })
    df.to_csv(
        f"{RUTA_SALIDA}/moran_por_region.csv", index=False,
        lineterminator="\n",
    )
    print(f"[moran_por_region.csv] {len(df)} filas")


def exportar_homofilia_por_sitio(conexion) -> None:
    df = consultar(conexion, "SELECT * FROM gini.homophily_by_site")
    df["bigregion"] = df["bigregion"].map(TRADUCCION_BIGREGION)
    df = df.rename(columns={
        "site_id_source": "sitio_id",
        "site_name": "nombre_sitio",
        "bigregion": "region_grande",
        "n_barrios": "cantidad_barrios",
        "gini_site": "gini_sitio",
        "gini_diff_medio": "diferencia_gini_promedio",
    })
    df.to_csv(
        f"{RUTA_SALIDA}/homofilia_por_sitio.csv", index=False,
        lineterminator="\n",
    )
    print(f"[homofilia_por_sitio.csv] {len(df)} filas")


def main() -> None:
    conexion = conectar()
    try:
        exportar_sitios(conexion)
        exportar_moran_por_region(conexion)
        exportar_homofilia_por_sitio(conexion)
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
