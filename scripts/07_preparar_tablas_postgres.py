"""Prepara sites.csv y site_neighborhoods.csv para cargar en PostgreSQL.

Lee SiteGiniLevel.csv y SiteGiniNeib.csv (crudos, en ingles, tal como
vienen de tDAR) y produce dos CSV intermedios en data/processed/ que
ya coinciden columna a columna con sql/01_esquema_postgres.sql.

Las dos tablas son independientes a proposito (decision del
07/09/2026): cruzar SiteGiniLevel con SiteGiniNeib por site_id
reconstruido solo da ~82% de match confiable, y ninguna de las dos
lineas de analisis lo necesita.
"""
import pandas as pd

RUTA_CRUDOS = "data/raw"
RUTA_PROCESADOS = "data/processed"

# Columnas nullable en el origen que deben exportarse como Int64 (y no
# como float64) para que PostgreSQL las acepte en columnas SMALLINT /
# INTEGER -- mismo problema que Int64 en el pipeline de Velasco: un
# entero con nulos se degrada a float64 y sale como "3.0", que
# PostgreSQL rechaza.
COLUMNAS_ENTERAS_SITES = [
    "which_level", "n_of_levels", "begin_date", "end_date", "count_hh",
]
COLUMNAS_ENTERAS_BARRIOS = [
    "count_hh", "neighborhood_begin_date", "neighborhood_end_date",
]

# Conteos esperados tras el ETL (con los CSV de tDAR descargados el
# 07/09/2026). Si estos numeros cambian, algo cambio rio arriba -- el
# dataset se actualizo, o se rompio un filtro -- y hay que revisarlo
# antes de recargar la base.
FILAS_ESPERADAS_SITES = 1171
FILAS_ESPERADAS_BARRIOS = 723


def _validar_gini_en_rango(df: pd.DataFrame, columnas: list[str]) -> None:
    """Corta el pipeline si alguna columna de Gini sale de [0, 1].

    Un Gini fuera de rango indicaria un error de carga o de calculo,
    no un resultado legitimo -- mejor fallar aca que exportar un CSV
    invalido para PostgreSQL (que ademas lo rechazaria por la
    constraint CHECK, pero con un mensaje mucho menos util).
    """
    for columna in columnas:
        fuera_de_rango = df[~df[columna].between(0, 1)]
        if not fuera_de_rango.empty:
            raise ValueError(
                f"{len(fuera_de_rango)} filas con {columna} fuera de "
                "[0, 1]"
            )


def preparar_sites() -> pd.DataFrame:
    """Limpia SiteGiniLevel.csv y arma la tabla gini.sites."""
    columnas_origen = {
        "Site": "site_name",
        "Bigregion": "bigregion",
        "Region": "region",
        "Subregion": "subregion",
        "Subarea": "subarea",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "WhichLevel": "which_level",
        "NOfLevels": "n_of_levels",
        "BeginDate": "begin_date",
        "EndDate": "end_date",
        "CountHH": "count_hh",
        "Gini": "gini",
        "Lower_B": "lower_b",
        "Upper_B": "upper_b",
    }
    df = pd.read_csv(f"{RUTA_CRUDOS}/SiteGiniLevel.csv", index_col=0)
    total_leido = len(df)

    sin_coordenadas = df[df["Latitude"].isna() | df["Longitude"].isna()]
    df = df.dropna(subset=["Latitude", "Longitude"])

    df = df.rename(columns=columnas_origen)[list(columnas_origen.values())]
    df[COLUMNAS_ENTERAS_SITES] = df[COLUMNAS_ENTERAS_SITES].astype("Int64")
    _validar_gini_en_rango(df, ["gini"])

    df.insert(0, "site_id", range(1, len(df) + 1))

    print("[sites] Filas leidas de SiteGiniLevel.csv:", total_leido)
    print(
        "[sites] Excluidas por falta de coordenadas:",
        len(sin_coordenadas), list(sin_coordenadas["Site"]),
    )
    print("[sites] Filas exportadas:", len(df))
    return df


def preparar_site_neighborhoods() -> pd.DataFrame:
    """Limpia SiteGiniNeib.csv y arma la tabla gini.site_neighborhoods."""
    columnas_origen = {
        "site_id": "site_id_source",
        "Site": "site_name",
        "Bigregion": "bigregion",
        "Region": "region",
        "Subregion": "subregion",
        "Subarea": "subarea",
        "Latitude": "latitude",
        "Longitude": "longitude",
        "HouseGroup": "house_group",
        "Count": "count_hh",
        "Gini_Site": "gini_site",
        "GiniNeib": "gini_neib",
        "Gini_Diff": "gini_diff",
        "BeginDate": "neighborhood_begin_date",
        "EndDate": "neighborhood_end_date",
    }
    df = pd.read_csv(f"{RUTA_CRUDOS}/SiteGiniNeib.csv", index_col=0)
    total_leido = len(df)

    df = df.rename(columns=columnas_origen)[list(columnas_origen.values())]
    # HouseGroup mezcla texto ("TP3", "I.ii") y numeros (200, 201): se
    # fuerza a texto para que un valor numerico no salga con notacion
    # cientifica o un ".0" colgado al exportar a CSV.
    df["house_group"] = df["house_group"].astype(str)
    df[COLUMNAS_ENTERAS_BARRIOS] = df[COLUMNAS_ENTERAS_BARRIOS].astype(
        "Int64"
    )
    _validar_gini_en_rango(df, ["gini_site", "gini_neib"])

    df.insert(0, "neighborhood_id", range(1, len(df) + 1))

    print("[site_neighborhoods] Filas leidas de SiteGiniNeib.csv:",
          total_leido)
    print("[site_neighborhoods] Filas exportadas:", len(df))
    return df


def main() -> None:
    sites = preparar_sites()
    barrios = preparar_site_neighborhoods()

    assert len(sites) == FILAS_ESPERADAS_SITES, (
        f"Se esperaban {FILAS_ESPERADAS_SITES} sitios, salieron "
        f"{len(sites)} -- revisar SiteGiniLevel.csv antes de recargar."
    )
    assert len(barrios) == FILAS_ESPERADAS_BARRIOS, (
        f"Se esperaban {FILAS_ESPERADAS_BARRIOS} barrios, salieron "
        f"{len(barrios)} -- revisar SiteGiniNeib.csv antes de recargar."
    )

    sites.to_csv(
        f"{RUTA_PROCESADOS}/sites.csv", index=False, lineterminator="\n"
    )
    barrios.to_csv(
        f"{RUTA_PROCESADOS}/site_neighborhoods.csv", index=False,
        lineterminator="\n",
    )


if __name__ == "__main__":
    main()
