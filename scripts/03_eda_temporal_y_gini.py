"""EDA pasos 3 y 4: cobertura temporal y distribucion del Gini.

BeginDate/EndDate estan en anos calendario (negativos = a.C.). No hay
que confundirlos con "Date", que es la fecha central usada para el
eje de los graficos de tendencia del paper (ver Fig. 1).
"""
import pandas as pd

RUTA = "data/raw/SiteGiniLevel.csv"
df = pd.read_csv(RUTA, index_col=0)

print("Cobertura temporal (BeginDate / EndDate, anos calendario):")
print(df[["BeginDate", "EndDate"]].describe())
print()

print("Sitios mas antiguos (BeginDate mas negativo):")
print(
    df.nsmallest(5, "BeginDate")[["Site", "Bigregion", "BeginDate", "EndDate"]]
)
print()

print("Distribucion del Gini:")
print(df["Gini"].describe())
print()

# Un Gini fuera de [0, 1] seria un error de calculo o de carga, no un
# resultado legitimo -- vale la pena chequearlo explicitamente en vez
# de confiar en que describe() lo hubiera mostrado con claridad.
fuera_de_rango = df[(df["Gini"] < 0) | (df["Gini"] > 1)]
print(f"Sitios con Gini fuera de [0, 1]: {len(fuera_de_rango)}")

print()
print("Gini por Bigregion (mediana, para no dejarnos enganar por outliers):")
print(df.groupby("Bigregion")["Gini"].median().sort_values(ascending=False))
