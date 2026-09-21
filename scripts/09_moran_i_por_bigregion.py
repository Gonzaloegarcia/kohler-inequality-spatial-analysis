"""Moran's I del Gini entre sitios, estratificado por Bigregion.

Linea 1 del angulo de reanalisis: el paper original no evalua si el
Gini de un sitio se relaciona con el de sus vecinos geograficos -- lo
reconoce como limitacion propia. Acá
lo probamos con un Moran's I global por region, usando k vecinos mas
cercanos (distancia de arco sobre la esfera, no euclidea plana, para
no distorsionar por la curvatura en regiones grandes como Asia).

Se estratifica por Bigregion (no global) porque un "vecino mas
cercano" sin restriccion geografica podria terminar en otro
continente para regiones con pocos sitios -- decision tomada con
Gonzalo el 07/09/2026.
"""
import os
import warnings

import numpy as np
import pandas as pd
import psycopg2
from esda.moran import Moran
from libpysal.weights import KNN
from sklearn.neighbors import BallTree

RADIO_TIERRA_KM = 6371.0

K_VECINOS = 5
# Minimo matematico: hace falta al menos K_VECINOS + 1 sitios para
# armar la matriz de vecinos.
MIN_SITIOS_PARA_CALCULAR = K_VECINOS + 1
# Mismo criterio que en el capstone de Velasco: por debajo de esto el
# resultado se muestra pero no se compara con el resto (es ruido).
MIN_SITIOS_CONFIABLE = 20
# esda.Moran no tiene parametro de semilla propio -- usa el generador
# aleatorio global de numpy para las permutaciones. Sin fijarla, el
# p-valor y el z-score cambian levemente entre corridas (mismo motivo
# por el que Velasco fija semilla para el jitter de coordenadas).
SEMILLA_PERMUTACIONES = 20250907


def conectar():
    return psycopg2.connect(
        dbname="kohler_gini", user="postgres",
        password=os.environ["PGPASSWORD"], host="localhost", port=5432,
    )


def leer_sites(conexion) -> pd.DataFrame:
    """Trae bigregion/longitude/latitude/gini de gini.sites.

    Se arma el DataFrame a mano desde el cursor (en vez de
    pd.read_sql con la conexion de psycopg2 directo) para evitar el
    UserWarning de pandas sobre conexiones DBAPI2 no soportadas, sin
    sumar SQLAlchemy como dependencia nueva solo para esto.
    """
    with conexion.cursor() as cursor:
        cursor.execute(
            "SELECT bigregion, longitude, latitude, gini FROM gini.sites"
        )
        filas = cursor.fetchall()
        columnas = [d.name for d in cursor.description]
    return pd.DataFrame(filas, columns=columnas)


def guardar_resultados(conexion, tabla: pd.DataFrame) -> None:
    """Persiste la tabla de resultados en gini.moran_by_region.

    DELETE + INSERT (no upsert) porque la tabla completa es chica (7
    filas como mucho, una por Bigregion) y este script siempre la
    recalcula entera -- no tiene sentido actualizar fila por fila.
    Idempotente: correr el script dos veces seguidas da el mismo
    resultado sin violar la PK.
    """
    # psycopg2 no sabe adaptar numpy.float64/int64 (los inserta como
    # texto literal "np.float64(...)" y rompe el SQL) -- hay que
    # convertir a tipos nativos de Python antes de pasarlos.
    filas = [
        (
            bigregion, int(fila["n_sitios"]), float(fila["moran_i"]),
            float(fila["p_valor"]), float(fila["z_score"]),
            int(fila["n_componentes"]),
            float(fila["dist_vecino_mediana_km"]),
            float(fila["dist_vecino_maxima_km"]),
            bool(fila["n_sitios"] >= MIN_SITIOS_CONFIABLE),
        )
        for bigregion, fila in tabla.iterrows()
    ]
    with conexion.cursor() as cursor:
        cursor.execute("DELETE FROM gini.moran_by_region")
        cursor.executemany(
            "INSERT INTO gini.moran_by_region VALUES "
            "(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            filas,
        )
    conexion.commit()


def distancias_al_vecino_mas_cercano(grupo: pd.DataFrame) -> np.ndarray:
    """Distancia (km) de cada sitio a su vecino mas cercano.

    Solo para diagnostico -- reportar que tan lejos esta el "vecino
    mas cercano" en regiones grandes (ej. Asia), donde podria terminar
    siendo un sitio a miles de km. BallTree con metrica haversine usa
    distancia de arco sobre la esfera, no euclidea plana.
    """
    coordenadas_rad = np.radians(grupo[["latitude", "longitude"]])
    arbol = BallTree(coordenadas_rad, metric="haversine")
    # k=2 porque el vecino mas cercano de un punto es el mismo punto
    # (distancia 0); el segundo resultado es el primer vecino real.
    distancias_rad, _ = arbol.query(coordenadas_rad, k=2)
    return distancias_rad[:, 1] * RADIO_TIERRA_KM


def moran_de_una_region(grupo: pd.DataFrame) -> dict:
    """Arma la matriz de k-vecinos-mas-cercanos y corre Moran's I.

    KNN con radius=RADIO_TIERRA_KM le pide a libpysal que calcule
    distancia de arco sobre la esfera en vez de distancia euclidea
    plana -- importante en regiones grandes, donde tratar lat/long
    como un plano cartesiano distorsiona las distancias reales cerca
    de los polos y en longitudes extremas.

    n_componentes > 1 significa que la red de vecinos se parte en
    subgrupos que no se conectan entre si (sitios aislados) -- se
    reporta como columna propia en vez de dejarlo como warning
    suelto de libpysal, porque afecta que tan confiable es el
    resultado.
    """
    coordenadas = grupo[["longitude", "latitude"]].to_numpy()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        pesos = KNN.from_array(
            coordenadas, k=K_VECINOS, radius=RADIO_TIERRA_KM
        )
    pesos.transform = "r"

    np.random.seed(SEMILLA_PERMUTACIONES)
    moran = Moran(grupo["gini"].to_numpy(), pesos, permutations=999)
    distancias_vecino = distancias_al_vecino_mas_cercano(grupo)
    return {
        "n_sitios": len(grupo),
        "moran_i": moran.I,
        "p_valor": moran.p_sim,
        "z_score": moran.z_sim,
        "n_componentes": pesos.n_components,
        "dist_vecino_mediana_km": np.median(distancias_vecino),
        "dist_vecino_maxima_km": np.max(distancias_vecino),
    }


def main() -> None:
    conexion = conectar()
    try:
        sites = leer_sites(conexion)

        resultados = {}
        excluidas = []
        for bigregion, grupo in sites.groupby("bigregion"):
            if len(grupo) < MIN_SITIOS_PARA_CALCULAR:
                excluidas.append((bigregion, len(grupo)))
                continue
            resultados[bigregion] = moran_de_una_region(grupo)

        tabla = pd.DataFrame(resultados).T.sort_values(
            "moran_i", ascending=False
        )
        guardar_resultados(conexion, tabla)
    finally:
        conexion.close()

    print(tabla.to_string(float_format=lambda x: f"{x:.4f}"))
    print()

    if excluidas:
        print(
            f"Regiones sin calcular (menos de {MIN_SITIOS_PARA_CALCULAR} "
            f"sitios, no alcanza para {K_VECINOS} vecinos): {excluidas}"
        )

    poco_confiables = tabla[tabla["n_sitios"] < MIN_SITIOS_CONFIABLE]
    if not poco_confiables.empty:
        print(
            f"Regiones con menos de {MIN_SITIOS_CONFIABLE} sitios -- "
            "mostrar en el mapa, no usar en comparaciones (mismo "
            "criterio que Udpinango/Agua Blanca en Velasco):",
            list(poco_confiables.index),
        )


if __name__ == "__main__":
    main()
