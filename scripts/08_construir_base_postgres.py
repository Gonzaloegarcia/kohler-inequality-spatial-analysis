"""Carga el esquema y los datos en la base kohler_gini.

Requiere que la base ya exista (createdb, ver mismo motivo que en
Velasco: CREATE DATABASE no corre dentro de una transaccion y
psycopg2 abre una implicita):

    $env:PGPASSWORD="..."
    & "C:\\Program Files\\PostgreSQL\\18\\bin\\createdb.exe" `
        -U postgres -h localhost kohler_gini

Y que scripts/07_preparar_tablas_postgres.py ya haya generado
data/processed/sites.csv y site_neighborhoods.csv.
"""
import os

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

RUTA_DDL = "sql/01_esquema_postgres.sql"
RUTA_PROCESADOS = "data/processed"

TABLAS = {
    "gini.sites": f"{RUTA_PROCESADOS}/sites.csv",
    "gini.site_neighborhoods": f"{RUTA_PROCESADOS}/site_neighborhoods.csv",
}


def config_conexion() -> dict:
    """Arma la config de conexion, leyendo PGPASSWORD recien al usarse.

    Si esto fuera una constante de modulo (evaluada al importar), un
    simple `import` de este script sin PGPASSWORD seteada explotaria
    con KeyError -- mala idea si algun dia otro script quiere
    reutilizar TABLAS o ejecutar_ddl sin conectarse todavia.
    """
    return {
        "dbname": "kohler_gini",
        "user": "postgres",
        "password": os.environ["PGPASSWORD"],
        "host": "localhost",
        "port": 5432,
    }


def ejecutar_ddl(conexion) -> None:
    # cursor.execute() sin parametros usa el protocolo "simple query"
    # de PostgreSQL, que si permite varias sentencias separadas por
    # ";" en un solo string -- por eso alcanza con leer el archivo
    # entero y ejecutarlo de una vez, sin partirlo por sentencia.
    with open(RUTA_DDL, encoding="utf-8") as archivo:
        ddl = archivo.read()
    with conexion.cursor() as cursor:
        cursor.execute(ddl)
    conexion.commit()


def cargar_tabla(conexion, tabla: str, ruta_csv: str) -> None:
    # NaN de pandas no es NULL de SQL: hay que convertirlo explicitamente
    # o psycopg2 intenta insertar el string literal "nan".
    df = pd.read_csv(ruta_csv).astype(object).where(pd.notna, None)
    columnas = ", ".join(df.columns)
    consulta = f"INSERT INTO {tabla} ({columnas}) VALUES %s"
    with conexion.cursor() as cursor:
        execute_values(cursor, consulta, df.itertuples(index=False))
    conexion.commit()
    print(f"[{tabla}] {len(df)} filas cargadas")


def main() -> None:
    conexion = psycopg2.connect(**config_conexion())
    try:
        ejecutar_ddl(conexion)
        for tabla, ruta_csv in TABLAS.items():
            cargar_tabla(conexion, tabla, ruta_csv)
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
