"""EDA de gini.site_neighborhoods -- Linea 2 (homofilia intra-sitio).

Objetivo: mas alla de confirmar el signo de gini_diff (ya lo hicimos
en el EDA inicial sobre el CSV crudo), entender que tan generalizado
es el patron, si depende del tamano del barrio (como sugiere el
material suplementario) y que region/sitios representan los casos mas
claros para contar la historia en Tableau.
"""
import os

import pandas as pd
import psycopg2


def conectar():
    return psycopg2.connect(
        dbname="kohler_gini", user="postgres",
        password=os.environ["PGPASSWORD"], host="localhost", port=5432,
    )


def leer_barrios(conexion) -> pd.DataFrame:
    with conexion.cursor() as cursor:
        cursor.execute("SELECT * FROM gini.site_neighborhoods")
        filas = cursor.fetchall()
        columnas = [d.name for d in cursor.description]
    return pd.DataFrame(filas, columns=columnas)


def guardar_resultados(conexion, con_varios_barrios: pd.DataFrame) -> None:
    """Persiste el detalle por sitio en gini.homophily_by_site.

    DELETE + INSERT: la tabla siempre se recalcula entera a partir de
    gini.site_neighborhoods, no tiene sentido actualizar fila por
    fila. Idempotente.

    Cast explicito a tipos nativos de Python: psycopg2 no sabe
    adaptar numpy.int64/float64 (los inserta como texto literal y
    rompe el SQL) -- itertuples() los devuelve tal cual salen de
    pandas, que son numpy, no Python puro.
    """
    tabla = con_varios_barrios.reset_index()
    filas = [
        (
            int(fila.site_id_source), fila.site_name, fila.bigregion,
            int(fila.n_barrios), float(fila.gini_site),
            float(fila.gini_diff_medio),
        )
        for fila in tabla.itertuples(index=False)
    ]
    with conexion.cursor() as cursor:
        cursor.execute("DELETE FROM gini.homophily_by_site")
        cursor.executemany(
            "INSERT INTO gini.homophily_by_site VALUES "
            "(%s, %s, %s, %s, %s, %s)",
            filas,
        )
    conexion.commit()


def main() -> None:
    conexion = conectar()
    try:
        barrios = leer_barrios(conexion)

        por_sitio = barrios.groupby(
            ["site_id_source", "site_name", "bigregion"]
        ).agg(
            n_barrios=("house_group", "nunique"),
            gini_site=("gini_site", "first"),
            gini_diff_medio=("gini_diff", "mean"),
        )
        # Con un solo barrio no hay nada contra que comparar
        # "homofilia entre barrios" -- es un caso limite del metodo,
        # no una excepcion real al patron (casos
        # Mohenjo-daro/J. Sprague/Cirencester).
        con_varios_barrios = por_sitio[por_sitio["n_barrios"] > 1]

        guardar_resultados(conexion, con_varios_barrios)
    finally:
        conexion.close()

    print("Sitios distintos por Bigregion (de los 83 con barrios):")
    print(
        barrios.groupby("bigregion")["site_id_source"].nunique()
        .sort_values(ascending=False)
    )
    print()

    print("gini_diff (barrio - sitio) por Bigregion -- mediana:")
    print(barrios.groupby("bigregion")["gini_diff"].median().sort_values())
    print()

    print("Correlacion entre tamano del barrio (count_hh) y gini_neib:")
    print(barrios[["count_hh", "gini_neib"]].corr().iloc[0, 1])
    print()

    un_solo_barrio = len(por_sitio) - len(con_varios_barrios)
    print(
        f"Sitios con un solo barrio (excluidos del ranking): "
        f"{un_solo_barrio} de {len(por_sitio)}"
    )
    print()

    print("Sitios con homofilia MAS fuerte (gini_diff mas negativo):")
    print(con_varios_barrios.sort_values("gini_diff_medio").head(5))
    print()

    print("Sitios donde el patron se INVIERTE (gini_diff positivo):")
    invertidos = con_varios_barrios[con_varios_barrios["gini_diff_medio"] > 0]
    print(f"{len(invertidos)} de {len(con_varios_barrios)} sitios")
    print(invertidos.sort_values("gini_diff_medio", ascending=False))
    print()

    print("Que tan universal es la homofilia POR REGION (sitios con >1")
    print("barrio unicamente):")
    con_region = con_varios_barrios.reset_index()
    resumen_region = con_region.groupby("bigregion").agg(
        n_sitios=("site_id_source", "nunique"),
        n_con_homofilia=("gini_diff_medio", lambda s: (s < 0).sum()),
        gini_diff_mediana=("gini_diff_medio", "median"),
    )
    resumen_region["pct_con_homofilia"] = (
        100 * resumen_region["n_con_homofilia"] / resumen_region["n_sitios"]
    )
    print(resumen_region.sort_values("pct_con_homofilia", ascending=False))


if __name__ == "__main__":
    main()
