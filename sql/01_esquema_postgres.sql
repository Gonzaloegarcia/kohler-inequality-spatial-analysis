-- Esquema PostgreSQL 18 -- sub-proyecto GINI (Kohler et al. 2025)
--
-- Requiere una base ya creada (CREATE DATABASE no corre dentro de una
-- transaccion, igual que en el capstone de Velasco):
--   createdb -U postgres -h localhost kohler_gini
--
-- Este esquema es independiente del proyecto Velasco a proposito
-- (decision de no mezclar con datos de Sierra del Velasco), por eso
-- vive en una base separada, no en un schema aparte dentro de
-- `velasco`.
--
-- ADVERTENCIA: destructivo. Volver a correr este archivo borra todo lo
-- que haya en el schema `gini` sin preguntar.

DROP SCHEMA IF EXISTS gini CASCADE;
CREATE SCHEMA gini;

-- -----------------------------------------------------------------
-- sites -- un sitio (sitio x fase temporal), de SiteGiniLevel.csv.
-- Unidad de analisis de la Linea 1 (autocorrelacion espacial del
-- Gini entre sitios, tipo Moran's I, estratificado por region).
-- -----------------------------------------------------------------
CREATE TABLE gini.sites (
    site_id       SMALLINT PRIMARY KEY,
    site_name     TEXT NOT NULL,
    bigregion     TEXT NOT NULL,
    region        TEXT NOT NULL,
    subregion     TEXT,
    subarea       TEXT,
    latitude      DOUBLE PRECISION NOT NULL,
    longitude     DOUBLE PRECISION NOT NULL,
    which_level   SMALLINT,
    n_of_levels   SMALLINT,
    begin_date    INTEGER NOT NULL,
    end_date      INTEGER NOT NULL,
    count_hh      SMALLINT NOT NULL,
    gini          DOUBLE PRECISION NOT NULL,
    lower_b       DOUBLE PRECISION,
    upper_b       DOUBLE PRECISION,
    CONSTRAINT gini_en_rango CHECK (gini BETWEEN 0 AND 1)
);

COMMENT ON TABLE gini.sites IS
    'Un sitio x fase, de SiteGiniLevel.csv (n=1176 en el CSV original). '
    'which_level + n_of_levels = "Social Advantage" (SA) del paper, no '
    'se materializa aca porque no la usan las dos lineas de analisis '
    'actuales -- calcular al vuelo si hace falta.';

COMMENT ON COLUMN gini.sites.latitude IS
    '5 sitios del CSV original no tienen coordenadas y se excluyeron '
    'en la carga (ninguno de Sudamerica).';

-- -----------------------------------------------------------------
-- site_neighborhoods -- un barrio (HouseGroup) dentro de un sitio,
-- de SiteGiniNeib.csv. Unidad de analisis de la Linea 2 (desigualdad
-- intra-sitio / homofilia entre barrios).
--
-- site_id_source NO es FK a sites.site_id: son dos tablas
-- independientes por decision de diseno (07/09/2026) -- cruzar
-- SiteGiniLevel con SiteGiniNeib por site_id reconstruido daba solo
-- ~82% de match confiable y ninguna de las dos lineas de analisis lo
-- necesita. site_id_source se conserva solo como referencia de
-- procedencia y porque SI agrupa bien los barrios de un mismo sitio
-- dentro de esta tabla.
-- -----------------------------------------------------------------
CREATE TABLE gini.site_neighborhoods (
    neighborhood_id         SMALLINT PRIMARY KEY,
    -- INTEGER a proposito, no SMALLINT como sites.site_id: los site_id
    -- originales de tDAR superan 32767 (ej. 117104), desbordarian un
    -- SMALLINT. No es una inconsistencia, es el rango real del dato.
    site_id_source          INTEGER NOT NULL,
    site_name               TEXT NOT NULL,
    bigregion               TEXT NOT NULL,
    region                  TEXT NOT NULL,
    subregion               TEXT,
    subarea                 TEXT,
    latitude                DOUBLE PRECISION NOT NULL,
    longitude               DOUBLE PRECISION NOT NULL,
    house_group             TEXT NOT NULL,
    count_hh                SMALLINT NOT NULL,
    gini_site               DOUBLE PRECISION NOT NULL,
    gini_neib               DOUBLE PRECISION NOT NULL,
    gini_diff               DOUBLE PRECISION NOT NULL,
    neighborhood_begin_date INTEGER NOT NULL,
    neighborhood_end_date   INTEGER NOT NULL,
    CONSTRAINT gini_site_en_rango CHECK (gini_site BETWEEN 0 AND 1),
    CONSTRAINT gini_neib_en_rango CHECK (gini_neib BETWEEN 0 AND 1)
);

-- site_id_source agrupa los barrios de un mismo sitio (ver comentario
-- de la tabla) -- es el patron de consulta mas probable, de ahi el
-- indice.
CREATE INDEX idx_site_neighborhoods_site_id_source
    ON gini.site_neighborhoods (site_id_source);

COMMENT ON TABLE gini.site_neighborhoods IS
    '723 filas de barrio (HouseGroup) dentro de 83 sitios, de '
    'SiteGiniNeib.csv. gini_diff = gini_neib - gini_site (signo '
    'verificado contra el dato real, no contra el nombre de la '
    'columna): negativo en ~84% de las filas, es decir el barrio '
    'suele ser menos desigual que el sitio completo (homofilia).';

COMMENT ON COLUMN gini.site_neighborhoods.neighborhood_begin_date IS
    'Ventana temporal del BARRIO, no de la fase del sitio -- distincion '
    'que costo descubrir con los casos El Trapiche/Ostia/Beer-Sheba. '
    'No usar para reconstruir fases de sitio.';

-- -----------------------------------------------------------------
-- moran_by_region -- resultado de la Linea 1 (Moran's I del Gini
-- entre sitios, k=5 vecinos, estratificado por Bigregion). A
-- diferencia de sites/site_neighborhoods, esta tabla NO se carga
-- desde un CSV de tDAR: la llena scripts/09_moran_i_por_bigregion.py
-- porque el calculo (permutaciones, distancia de arco) requiere
-- esda/libpysal en Python -- PostgreSQL no tiene estadistica espacial
-- nativa sin PostGIS, que este servidor no tiene instalado (mismo
-- motivo que la reproyeccion de coordenadas en Velasco).
-- -----------------------------------------------------------------
CREATE TABLE gini.moran_by_region (
    bigregion               TEXT PRIMARY KEY,
    n_sitios                SMALLINT NOT NULL,
    moran_i                 DOUBLE PRECISION NOT NULL,
    p_valor                 DOUBLE PRECISION NOT NULL,
    z_score                 DOUBLE PRECISION NOT NULL,
    n_componentes           SMALLINT NOT NULL,
    dist_vecino_mediana_km  DOUBLE PRECISION NOT NULL,
    dist_vecino_maxima_km   DOUBLE PRECISION NOT NULL,
    confiable               BOOLEAN NOT NULL
);

COMMENT ON TABLE gini.moran_by_region IS
    'Un Moran''s I global por Bigregion (k=5 vecinos, distancia de '
    'arco, 999 permutaciones, semilla fija). confiable = FALSE cuando '
    'n_sitios < 20 (mismo criterio que Udpinango/Agua Blanca en '
    'Velasco) -- hoy solo Africa (n=12, vecino mas lejano 6208 km).';

-- -----------------------------------------------------------------
-- homophily_by_site -- resultado de la Linea 2 (homofilia
-- intra-sitio), un registro por sitio con mas de un barrio. Tampoco
-- se carga desde tDAR: la llena
-- scripts/10_eda_homofilia_intra_sitio.py agregando gini.
-- site_neighborhoods a nivel de sitio. Los sitios con un solo barrio
-- (16 de 83) se excluyen de origen -- no hay nada contra que comparar
-- homofilia con un unico barrio.
-- -----------------------------------------------------------------
CREATE TABLE gini.homophily_by_site (
    site_id_source   INTEGER PRIMARY KEY,
    site_name        TEXT NOT NULL,
    bigregion        TEXT NOT NULL,
    n_barrios        SMALLINT NOT NULL,
    gini_site        DOUBLE PRECISION NOT NULL,
    gini_diff_medio  DOUBLE PRECISION NOT NULL,
    CONSTRAINT n_barrios_minimo CHECK (n_barrios > 1)
);

COMMENT ON TABLE gini.homophily_by_site IS
    'gini_diff_medio = promedio de (gini_neib - gini_site) entre los '
    'barrios del sitio. Negativo = homofilia (barrios mas homogeneos '
    'que el sitio completo). Universal o casi en las 6 regiones con '
    'datos (85.7% a 100% de los sitios) -- Africa no tiene ningun '
    'sitio en esta tabla (0 en SiteGiniNeib.csv).';
