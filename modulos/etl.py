import sys
sys.path.append(".")

import os
import pandas as pd
import matplotlib.pyplot as plt
from config import (RUTA_ENVIO_DATOS, CARPETA_SALIDAS, PREFIJO_REPORTE, ENCODING_CSV, ESTADO_CRITICO, ESTADOS_ENVIO,
                    ZONA_ALERTAS_VIALES, DIAS_SEMANA, COLUMNAS_OBLIGATORIAS, COLUMNAS_NUMERICAS, COLUMNAS_CLIMA,
                    COLUMNAS_ALERTAS, COLUMNAS_REPORTE, COLUMNAS_CALIDAD)
from modulos.metricas import inspeccionar_df, porcentaje_criticos_por_zona, demora_promedio_por_zona


# ===== EXTRACCIÓN =====

# N19 y N20
def extraer_datos(lista_envios, lista_clima, alertas_viales):
    df_envios = pd.DataFrame(lista_envios)
    # columns= hace que, sin internet, los DataFrames vacíos tengan columnas y el merge no falle
    df_clima = pd.DataFrame(lista_clima, columns=COLUMNAS_CLIMA)
    df_alertas = pd.DataFrame(alertas_viales, columns=COLUMNAS_ALERTAS)
    return df_envios, df_clima, df_alertas

# N21
def leer_archivo(ruta):
    if ruta.endswith(".json"):
        return pd.read_json(ruta)
    if ruta.endswith(".xlsx"):
        return pd.read_excel(ruta)
    if ruta.endswith(".csv"):
        return pd.read_csv(ruta, encoding=ENCODING_CSV)
    if ruta.endswith(".csv.gz"):
        return pd.read_csv(ruta, compression="gzip", encoding=ENCODING_CSV)
    if ruta.endswith(".zip"):
        return pd.read_csv(ruta, compression="zip", encoding=ENCODING_CSV)
    raise ValueError(f"Formato de archivo no soportado: {ruta}")

# N19 y N21
def comparar_con_fuente(df_envios, ruta=RUTA_ENVIO_DATOS):
    # Solo se compara: limpiar el archivo otra vez duplicaría la lógica de envios.py
    df_archivo = leer_archivo(ruta)
    # N20: df_archivo["id"] es una Series y .str limpia toda la columna sin recorrerla con un for
    ids_repetidos = df_archivo["id"].str.strip().str.upper().duplicated().sum()
    rechazados = len(df_archivo) - len(df_envios)
    print(f"Archivo fuente: {len(df_archivo)} filas | cargadas: {len(df_envios)} | "
          f"rechazadas: {rechazados} ({ids_repetidos} por id repetido)")
    assert rechazados >= 0, "Hay más envíos cargados que filas en el archivo fuente"


# ===== TRANSFORMACIÓN =====

# N20 y N22
def convertir_fechas(df):
    # La columna mezcla formatos. Convertir todo junto pierde fechas o invierte día y mes sin avisar,
    # por eso se convierte cada formato por separado. Lo que no es fecha queda NaT, no se inventa.
    fechas_iso = pd.to_datetime(df["fecha_despacho"], format="%Y-%m-%d", errors="coerce")
    fechas_dia_mes = pd.to_datetime(df["fecha_despacho"], format="%d/%m/%Y", errors="coerce")
    df["fecha_despacho"] = fechas_iso.fillna(fechas_dia_mes)
    df["anio_despacho"] = df["fecha_despacho"].dt.year
    df["mes_despacho"] = df["fecha_despacho"].dt.month
    df["dia_despacho"] = df["fecha_despacho"].dt.day
    df["dia_semana_despacho"] = df["fecha_despacho"].dt.day_name().map(DIAS_SEMANA)
    return df

# N20
def convertir_tipos(df):
    for columna in COLUMNAS_NUMERICAS:
        df[columna] = pd.to_numeric(df[columna], errors="coerce")
    return df

# N20
def marcar_nulos(df):
    # No se imputa con 0: una demora de 0 afirmaría "llegó en tiempo" cuando en realidad no se sabe,
    # y además bajaría el promedio de metricas.py. mean() ignora los nulos, así que el promedio no cambia.
    sin_horas = df["demora_horas"].isna()
    # distancia_km queda nula solo si el destino no está en CIUDADES (por ejemplo, Narnia)
    destino_desconocido = df["distancia_km"].isna()
    df["datos_incompletos"] = sin_horas | destino_desconocido
    df["fecha_invalida"] = df["fecha_despacho"].isna()
    return df

# N20
def agregar_columnas_calculadas(df):
    # Función por columna: .map() aplica el diccionario a toda la Series de estados
    estados = df["estado"]
    df["severidad"] = estados.map(ESTADOS_ENVIO)
    # Operación vectorizada. A diferencia de demora_horas, negativo significa que va adelantado
    df["diferencia_horas"] = df["horas_transcurridas"] - df["horas_estimadas"]
    return df

# N20
def transformar_envios(df_crudo):
    df = df_crudo.copy()
    df = convertir_fechas(df)
    df = convertir_tipos(df)
    df = marcar_nulos(df)
    df = agregar_columnas_calculadas(df)
    return df

# N22 y criterio de aceptación 2
def combinar_clima(df_envios, df_clima):
    clima = df_clima.rename(columns={"descripcion": "descripcion_clima"})
    # left: se conservan todos los envíos aunque no haya clima para su destino.
    # many_to_one: muchos envíos por destino y una fila de clima por destino; si no se cumple, Pandas corta.
    df = df_envios.merge(clima, on="destino", how="left", validate="many_to_one", indicator="cruce_clima")
    assert len(df) == len(df_envios), "El merge con clima cambió la cantidad de filas"
    # Sin dato de clima no es lo mismo que "no llueve": lluvia_fuerte queda nula y se marca aparte
    df["clima_disponible"] = df["cruce_clima"] == "both"
    sin_clima = df[~df["clima_disponible"]]
    print(f"Envíos sin datos de clima: {len(sin_clima)} {sin_clima['destino'].unique().tolist()}")
    return df.drop(columns="cruce_clima")

# N22 y criterio de aceptación 2
def combinar_alertas(df_envios, df_alertas):
    # Las alertas no tienen clave por envío: unirlas directo sería muchos a muchos y multiplicaría filas.
    # Primero se resumen a una fila por zona y después se unen por zona.
    alertas = df_alertas.copy()
    alertas["zona"] = ZONA_ALERTAS_VIALES
    resumen = alertas.groupby("zona", as_index=False).agg(
        cantidad_alertas=("titulo", "count"),
        primera_alerta_portal=("titulo", "first"),
    )
    df = df_envios.merge(resumen, on="zona", how="left", validate="many_to_one", indicator="cruce_alertas")
    assert len(df) == len(df_envios), "El merge con alertas cambió la cantidad de filas"
    # No se completa con 0: las noticias son solo de la Ciudad de Buenos Aires, del resto no se sabe
    print(f"Envíos con alertas viales de su zona: {(df['cruce_alertas'] == 'both').sum()}")
    return df.drop(columns="cruce_alertas")

# N22
def resumir_por_estado_y_zona(df):
    resumen = df.groupby(["zona", "estado", "severidad"], as_index=False).agg(cantidad=("id", "count"))
    assert resumen["cantidad"].sum() == len(df), "El resumen por estado y zona perdió filas"
    return resumen.sort_values(by=["severidad", "cantidad"], ascending=False).reset_index(drop=True)

# N22
def resumir_por_dia_despacho(df):
    # groupby excluye los NaT, por eso acá solo cuentan los envíos con fecha válida
    resumen = df.groupby("dia_semana_despacho", as_index=False).agg(
        cantidad=("id", "count"),
        demora_promedio_horas=("demora_horas", "mean"),
    )
    assert resumen["cantidad"].sum() == df["fecha_despacho"].notna().sum(), "El resumen por día perdió filas"
    return resumen.sort_values(by="cantidad", ascending=False).reset_index(drop=True)

# N22
def resumir_zonas_con_join(df):
    # join une por índice: las dos tablas de metricas.py quedan lado a lado usando la zona como índice
    criticos = porcentaje_criticos_por_zona(df).set_index("zona")
    demoras = demora_promedio_por_zona(df).set_index("zona")
    return criticos.join(demoras)

# Criterio de aceptación 1
def generar_reporte_criticos(df):
    criticos = df[df["estado"] == ESTADO_CRITICO]
    reporte = criticos[COLUMNAS_REPORTE].sort_values(by="demora_horas", ascending=False)
    return reporte.reset_index(drop=True)

# N20
def generar_reporte_calidad(df):
    return df[df["datos_incompletos"]][COLUMNAS_CALIDAD].reset_index(drop=True)

# N19
def validar_transformacion(df_crudo, df):
    assert len(df) == len(df_crudo), "La transformación cambió la cantidad de filas"
    assert df["id"].notna().all(), "Hay envíos sin id"
    assert df["id"].is_unique, "Hay ids de envío repetidos"
    assert df["severidad"].notna().all(), "Hay estados que no están en ESTADOS_ENVIO"
    for columna in COLUMNAS_OBLIGATORIAS:
        assert columna in df.columns, f"Falta la columna {columna}, metricas.py la necesita"


# ===== CARGA =====

# N19, N21 y criterio de aceptación 1
def exportar_reporte(reporte, carpeta, fecha):
    # La fecha en el nombre es lo que lo vuelve un reporte diario
    base = os.path.join(carpeta, f"{PREFIJO_REPORTE}{fecha}")
    rutas = {
        "csv": base + ".csv",
        "excel": base + ".xlsx",
        "json": base + ".json",
        "csv_comprimido": base + ".csv.gz",
    }
    # index=False: el índice no es un dato, no tiene que salir como columna.
    # utf-8-sig: para que Excel en Windows muestre bien las tildes.
    reporte.to_csv(rutas["csv"], index=False, encoding=ENCODING_CSV)
    reporte.to_excel(rutas["excel"], index=False, sheet_name="Criticos")
    # records: un objeto por fila. force_ascii=False: conserva las tildes.
    reporte.to_json(rutas["json"], orient="records", indent=2, force_ascii=False)
    reporte.to_csv(rutas["csv_comprimido"], index=False, encoding=ENCODING_CSV, compression="gzip")
    return rutas

# N19 y N21
def validar_carga(reporte, rutas):
    # Se relee cada archivo y se compara con lo exportado: si no coincide, hay un bug de exportación
    for ruta in rutas.values():
        releido = leer_archivo(ruta)
        assert len(releido) == len(reporte), f"Las filas de {ruta} no coinciden con lo exportado"
        if len(reporte) > 0:
            assert list(releido.columns) == COLUMNAS_REPORTE, f"Las columnas de {ruta} no coinciden"
            assert set(releido["id"]) == set(reporte["id"]), f"Los ids de {ruta} no coinciden"

# N22
def listar_reportes(carpeta):
    # El nombre lleva la fecha como AAAA-MM-DD, así que ordenar el texto es ordenar por fecha
    reportes = []
    for nombre in os.listdir(carpeta):
        if nombre.startswith(PREFIJO_REPORTE) and nombre.endswith(".csv"):
            reportes.append(nombre)
    return sorted(reportes)

# N22
def actualizar_historial(carpeta):
    # concat reúne bloques con las mismas columnas. Se llama una sola vez, fuera del for.
    bloques = []
    for nombre in listar_reportes(carpeta):
        bloque = leer_archivo(os.path.join(carpeta, nombre))
        if len(bloque) > 0:
            bloque["fecha_reporte"] = nombre[len(PREFIJO_REPORTE):-len(".csv")]
            bloques.append(bloque)
    if len(bloques) == 0:
        return pd.DataFrame(columns=COLUMNAS_REPORTE + ["fecha_reporte"])
    return pd.concat(bloques, ignore_index=True)

# N22
def comparar_con_dia_anterior(reporte, carpeta, fecha):
    anteriores = []
    for nombre in listar_reportes(carpeta):
        if nombre < f"{PREFIJO_REPORTE}{fecha}.csv":
            anteriores.append(nombre)
    if len(anteriores) == 0:
        print("No hay un reporte anterior para comparar (primer día)")
        return None

    # El último de la lista es el más reciente. outer conserva los ids de los dos días
    # y _merge dice en cuál estaba cada uno: left_only = hoy, right_only = antes, both = los dos.
    anterior = leer_archivo(os.path.join(carpeta, anteriores[-1]))
    comparacion = reporte[["id"]].merge(anterior[["id"]], on="id", how="outer", validate="one_to_one", indicator=True)
    comparacion["situacion"] = comparacion["_merge"].astype(str).map(
        {"left_only": "Nuevo", "right_only": "Resuelto", "both": "Persistente"})
    print(f"Comparación contra {anteriores[-1]}: {comparacion['situacion'].value_counts().to_dict()}")
    return comparacion[["id", "situacion"]]

# N23
def graficar_ranking_criticos(df, ruta):
    # Barras horizontales para comparar zonas. Ascendente porque barh dibuja de abajo hacia arriba:
    # así la zona con más críticos queda primera.
    ranking = porcentaje_criticos_por_zona(df).sort_values(by="porcentaje_criticos")
    ax = ranking.plot(kind="barh", x="zona", y="porcentaje_criticos", legend=False,
                      title="Porcentaje de envíos críticos por zona")
    ax.set_xlabel("Envíos críticos (%)")
    ax.set_ylabel("Zona")
    ax.set_xlim(0, 100)
    plt.tight_layout()
    plt.savefig(ruta)
    plt.close()


# ===== ORQUESTADOR =====

# N19: devuelve el DataFrame para metricas.py y las rutas para adjuntar el reporte en notificaciones.py
def ejecutar_etl(lista_envios, lista_clima, alertas_viales, carpeta=CARPETA_SALIDAS, fecha=None):
    if fecha is None:
        fecha = pd.Timestamp.today().strftime("%Y-%m-%d")

    # Extracción: df_envios_crudo queda sin tocar porque transformar_envios trabaja sobre una copia
    print("\n=== ETL: extracción ===")
    df_envios_crudo, df_clima, df_alertas = extraer_datos(lista_envios, lista_clima, alertas_viales)
    print(f"Envíos: {len(df_envios_crudo)} | clima: {len(df_clima)} | alertas: {len(df_alertas)}")
    inspeccionar_df(df_envios_crudo)
    comparar_con_fuente(df_envios_crudo)

    # Transformación
    print("\n=== ETL: transformación ===")
    df = transformar_envios(df_envios_crudo)
    df = combinar_clima(df, df_clima)
    df = combinar_alertas(df, df_alertas)
    validar_transformacion(df_envios_crudo, df)
    print(f"Fechas válidas: {df['fecha_despacho'].notna().sum()} | inválidas: {df['fecha_invalida'].sum()} | "
          f"envíos con datos incompletos: {df['datos_incompletos'].sum()}")
    print("\nEnvíos por estado y zona:")
    print(resumir_por_estado_y_zona(df))
    print("\nEnvíos por día de despacho:")
    print(resumir_por_dia_despacho(df))
    print("\nResumen por zona:")
    print(resumir_zonas_con_join(df))
    reporte = generar_reporte_criticos(df)
    calidad = generar_reporte_calidad(df)

    # Carga: siempre en la carpeta de salidas, nunca sobre datos/
    print("\n=== ETL: carga ===")
    os.makedirs(carpeta, exist_ok=True)
    rutas = exportar_reporte(reporte, carpeta, fecha)
    validar_carga(reporte, rutas)
    print(f"Reporte de críticos: {len(reporte)} filas exportadas y validadas")

    rutas["calidad"] = os.path.join(carpeta, f"revision_datos_{fecha}.csv")
    calidad.to_csv(rutas["calidad"], index=False, encoding=ENCODING_CSV)
    print(f"Envíos para revisar por datos incompletos: {len(calidad)}")

    comparacion = comparar_con_dia_anterior(reporte, carpeta, fecha)
    if comparacion is not None:
        rutas["comparacion"] = os.path.join(carpeta, f"comparacion_criticos_{fecha}.csv")
        comparacion.to_csv(rutas["comparacion"], index=False, encoding=ENCODING_CSV)

    rutas["historial"] = os.path.join(carpeta, "historial_criticos.csv")
    actualizar_historial(carpeta).to_csv(rutas["historial"], index=False, encoding=ENCODING_CSV)

    rutas["grafico"] = os.path.join(carpeta, f"ranking_criticos_{fecha}.png")
    graficar_ranking_criticos(df, rutas["grafico"])

    print("Archivos generados:")
    for ruta in rutas.values():
        print(f"- {ruta}")
    return df, rutas

if __name__ == "__main__":
    from modulos.envios import cargar_envios
    # Prueba sin internet: sin clima ni alertas el programa tiene que funcionar igual
    df_prueba, rutas_prueba = ejecutar_etl(cargar_envios(), [], [])
    print(df_prueba[["id", "fecha_despacho", "datos_incompletos", "severidad"]])
