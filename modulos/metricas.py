import sys
sys.path.append(".")

import pandas as pd
import matplotlib.pyplot as plt
from config import ESTADO_CRITICO

# N20
def inspeccionar_df(df):
    print("Filas y columnas:", df.shape)
    print(df.dtypes)
    nulos = df.isna().sum()
    print("Columnas con nulos:")
    print(nulos[nulos > 0])

# N20
def conteo_por_estado(df):
    return df["estado"].value_counts()

def porcentaje_criticos_por_zona(df):
    datos = df.copy()
    datos["es_critico"] = datos["estado"] == ESTADO_CRITICO
    resumen = datos.groupby("zona", as_index=False).agg(
        total_envios=("id", "count"),
        criticos=("es_critico", "sum"),
    )
    resumen["porcentaje_criticos"] = resumen["criticos"] / resumen["total_envios"] * 100
    return resumen.sort_values(by="porcentaje_criticos", ascending=False)

def demora_promedio_por_zona(df):
    resumen = df.groupby("zona", as_index=False).agg(demora_promedio_horas=("demora_horas", "mean"))
    return resumen.sort_values(by="demora_promedio_horas", ascending=False)

def indicadores_generales(df):
    criticos = (df["estado"] == ESTADO_CRITICO).sum()
    return {
        "total_envios": len(df),
        "porcentaje_criticos": criticos / len(df) * 100,
        "demora_promedio_horas": df["demora_horas"].mean(),
        "cumplimiento_promedio": df["cumplimiento"].mean(),
    }

def graficar_estados(df):
    conteo = conteo_por_estado(df)
    ax = conteo.plot(kind="bar", title="Estados de los envíos")
    ax.set_xlabel("Estado")
    ax.set_ylabel("Cantidad de envíos")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    from modulos.envios import cargar_envios
    df_prueba = pd.DataFrame(cargar_envios())
    inspeccionar_df(df_prueba)
    print(porcentaje_criticos_por_zona(df_prueba))
    print(demora_promedio_por_zona(df_prueba))
    print(indicadores_generales(df_prueba))
    graficar_estados(df_prueba)