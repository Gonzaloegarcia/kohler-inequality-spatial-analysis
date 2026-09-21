# ArqueoData — Desigualdad GINI (Kohler et al. 2025)

🇬🇧 [Read this in English](README.en.md)

Re-análisis propio de un dataset arqueológico público (>1.100 sitios,
>47.000 unidades residenciales, escala global) sobre desigualdad
económica medida como coeficiente de Gini del tamaño de vivienda. No es
un resumen del paper: el ángulo —contagio espacial de la desigualdad
entre sitios vecinos— es un hueco que el propio paper reconoce no haber
explorado.

![Dashboard: mapa de sitios, Moran's I por región y agrupamiento por similitud intra-sitio](assets/dashboard.jpg)

**Dashboard interactivo:** https://public.tableau.com/app/profile/gonzalo.enrique.garcia/viz/Tableau_kohler_2025/Dashboard1

## Pregunta de investigación

¿El coeficiente de Gini de un sitio arqueológico se relaciona con el de
sus vecinos geográficos? El paper principal mide desigualdad sitio por
sitio y reconoce explícitamente que "no toma en cuenta posibles
conexiones con jerarquías de asentamiento vecinas" — ese es el hueco que
este proyecto llena.

## Hallazgo principal

Con un Moran's I global (k=5 vecinos más cercanos, distancia de arco,
999 permutaciones) estratificado por región, la desigualdad se
correlaciona positiva y significativamente con la de los vecinos
geográficos en las 6 regiones con muestra confiable (n ≥ 20):

| Región | n | Moran's I | p-valor |
|---|---|---|---|
| Sudamérica | 54 | 0,474 | 0,001 |
| Oceanía | 24 | 0,390 | 0,002 |
| Mesoamérica | 155 | 0,335 | 0,001 |
| Asia | 265 | 0,305 | 0,001 |
| Norteamérica | 276 | 0,242 | 0,001 |
| Europa | 385 | 0,209 | 0,001 |

África se excluye del análisis (n=12, vecino más cercano a más de 6.000
km en promedio — no hay estructura espacial real que medir con esa
dispersión). Sudamérica tiene el efecto más fuerte y los vecinos más
próximos entre sí (mediana 5,9 km).

Como línea secundaria, el dashboard también muestra agrupamiento por
similitud dentro de un mismo sitio (barrios de status económico
parecido tienden a ubicarse juntos), usando el dataset `SiteGiniNeib`
del mismo proyecto.

## Stack técnico

- **Python** (pandas, numpy, scikit-learn, libpysal, esda) — limpieza,
  preparación de tablas y cálculo de Moran's I.
- **PostgreSQL** — esquema `gini` en base propia (`kohler_gini`),
  independiente del resto de proyectos de ArqueoData.
- **Tableau Public** — dashboard final.

## Sobre los datos y su licencia

Este repositorio **no incluye ningún CSV**, ni el dataset original de
tDAR ni los archivos que produce el propio pipeline.

**El dataset original es de acceso abierto** (requiere solo una cuenta
gratuita en tDAR) y se puede descargar acá, con la atribución que
corresponde a los autores originales:

- **Dataset:** Ortman, S., Kohler, T.A., Bogaard, A. *SiteGiniLevel*
  (tDAR id: 502392). Colección completa (9 datasets):
  https://core.tdar.org/collection/72000/gini-project-data-files
- **Paper principal:** Kohler, T.A., Bogaard, A., Ortman, S.G. et al.
  2025. "Economic inequality is fueled by population scale,
  land-limited production, and settlement hierarchies across the
  archaeological record." *PNAS* 122(16), e2400691122.
  https://doi.org/10.1073/pnas.2400691122
- **Introducción de la Special Feature:** Kohler, T.A., Bogaard, A.,
  Ortman, S.G. 2025. "Introducing the Special Feature on housing
  differences and inequality over the very long term." *PNAS*
  122(16), e2401989122.

## Estructura del repositorio

```
scripts/
  01-06_eda_*.py                        EDA sobre los CSV crudos de tDAR
  07_preparar_tablas_postgres.py        limpieza + tablas listas para cargar
  08_construir_base_postgres.py         carga el esquema y los datos
  09_moran_i_por_bigregion.py           Moran's I estratificado por región
  10_eda_homofilia_intra_sitio.py       EDA de agrupamiento por similitud
  11_exportar_tableau.py                exporta las vistas para Tableau
sql/
  01_esquema_postgres.sql               DDL del schema `gini`
Tableau_kohler_2025.twb                 workbook de Tableau (referencia; los
                                        paths a los datos no van a resolver
                                        sin el pipeline corrido localmente)
```

## Cómo correr el pipeline

Requiere los 9 CSV originales de tDAR (no incluidos, ver arriba,
descargables gratis con cuenta propia) y una instancia de PostgreSQL
local.

```bash
pip install -r requirements.txt

# 1-6. EDA (opcional, solo exploración)
python scripts/01_eda_site_gini_level.py
# ...

# 7. Preparar tablas intermedias
python scripts/07_preparar_tablas_postgres.py

# 8. Crear la base (una sola vez) y cargar esquema + datos
$env:PGPASSWORD="..."
createdb -U postgres -h localhost kohler_gini
python scripts/08_construir_base_postgres.py

# 9-10. Análisis (Moran's I, homofilia)
python scripts/09_moran_i_por_bigregion.py
python scripts/10_eda_homofilia_intra_sitio.py

# 11. Exportar para Tableau
python scripts/11_exportar_tableau.py
```

## Limitaciones declaradas

- El tamaño de vivienda es un **piso**, no el techo, de la desigualdad
  real — el propio paper lo aclara (no captura riqueza mueble, acceso a
  recursos, etc.).
- África queda fuera de cualquier comparación por muestra insuficiente
  (n=12) y dispersión geográfica extrema.
- El dataset agrupa Chipre bajo `Bigregion = Asia` por convención
  arqueológica (esfera de intercambio del Cercano Oriente), no
  geografía política — y tiene una inconsistencia interna sin corregir
  entre dos sitios chipriotas (Khirokitia, Marki Alonia) etiquetados
  como `Europe` con el mismo `Region` que el resto. No se corrigió a
  mano por no ser especialistas regionales.

## Autor

Gonzalo García — [Tableau Public](https://public.tableau.com/app/profile/gonzalo.enrique.garcia)
