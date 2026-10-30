import sys
sys.path.append(".")

import pandas as pd
from config import (RUTA_ENVIO_DATOS, URLS_NOVEDADES_VIALES, SITIOS_WEB, API_KEY_CLIMA, ESTADO_CRITICO,
                    ZONA_ALERTAS_VIALES)
from modulos.apis import consultar_clima_ciudad, obtener_clima_destinos, enviar_alerta_post
from modulos.etl import ejecutar_etl
from modulos.envios import cargar_envios, evaluar_riesgo_envio, generar_mensaje_cliente, armar_asunto_email, filtrar_por_estado
from modulos.metricas import (inspeccionar_df, porcentaje_criticos_por_zona, demora_promedio_por_zona,
                              indicadores_generales, graficar_estados)
from modulos.scraping import obtener_html, registrar_sitio, ejemplos_find_all, buscar_alertas_viales

def ejecutar_plataforma():
    alertas_viales = []
    html_noticias = None
    for url in URLS_NOVEDADES_VIALES:
        html_noticias = obtener_html(url)
        if html_noticias is not None:
            print("Criterios de find_all:", ejemplos_find_all(html_noticias))
            alertas_viales += buscar_alertas_viales(html_noticias)

    print("\n=== Sitios registrados ===")
    for nombre in SITIOS_WEB:
        if nombre == "noticias":
            sitio = registrar_sitio(nombre, html_noticias)
        else:
            sitio = registrar_sitio(nombre)
        print(f"- {sitio['dominio']} | IP: {sitio['ip']} | navegador: {sitio['navegador']}")
    print(f"\nAlertas viales encontradas: {len(alertas_viales)}")
    if len(alertas_viales) > 0:
        print(pd.DataFrame(alertas_viales)[["fecha", "titulo"]])  

    lista_envios = cargar_envios(RUTA_ENVIO_DATOS)
    if len(lista_envios) == 0:
        print("No hay envíos para procesar")
        return

    destinos = []
    for envio in lista_envios:
        destinos.append(envio["destino"])
    lista_clima = obtener_clima_destinos(destinos)
    clima_por_destino = {}
    for clima in lista_clima:
        clima_por_destino[clima["destino"]] = clima
    if len(lista_clima) > 0:
        print("\n=== Clima por destino ===")
        print(pd.DataFrame(lista_clima))  

    # N17
    clima_owm_por_destino = {}
    if API_KEY_CLIMA != "":
        for destino in clima_por_destino:
            clima_owm = consultar_clima_ciudad(destino, API_KEY_CLIMA)
            if clima_owm is not None:
                clima_owm_por_destino[destino] = clima_owm
    else:
        print("OpenWeatherMap sin configurar (falta claves.py), se usa solo Open-Meteo")

    print("\n=== Envíos ===")
    for envio in lista_envios:
        clima = clima_por_destino.get(envio["destino"])
        if clima is not None and clima["lluvia_fuerte"]:
            envio["riesgo_clima"] = "Lluvia Fuerte"
        elif clima is not None:
            envio["riesgo_clima"] = f"{clima['descripcion']} ({clima['temperatura']}°C)"
        if envio["zona"] == ZONA_ALERTAS_VIALES:
            evaluar_riesgo_envio(envio, alertas_viales)
        else:
            evaluar_riesgo_envio(envio)

        print(f"- {envio['id']} de {envio['cliente']} -> {envio['destino']} (zona {envio['zona']})")
        print(f"  Clima: {envio['riesgo_clima']} | Estado: {envio['estado']} | Prioridad: {envio['prioridad']}")
        clima_owm = clima_owm_por_destino.get(envio["destino"])
        if clima_owm is not None:
            print(f"  OpenWeatherMap: {clima_owm['descripcion']} ({clima_owm['temperatura']}°C)")
        if not envio["email_valido"]:
            print("  Email inválido: no se puede avisar al cliente")
        elif envio["estado"] != "En término":
            print(f"  Asunto: {armar_asunto_email(envio)}")
            print(f"  Mensaje: {generar_mensaje_cliente(envio)}")

    criticos = filtrar_por_estado(lista_envios, ESTADO_CRITICO)
    print(f"\n=== Envíos críticos ({len(criticos)}) ===")
    for envio in criticos:
        print(f"- {envio['id']} | {envio['cliente']} | zona {envio['zona']} | "
              f"causa: {envio['causa']} | acción: {envio['accion_recomendada']}")

    # N15
    enviadas = 0
    for envio in criticos:
        if enviar_alerta_post(envio) is not None:
            enviadas += 1
    print(f"Alertas enviadas por POST: {enviadas} de {len(criticos)}")

    # N19: va después de evaluar los riesgos para que estado, causa y acción ya existan
    df_envios, rutas_etl = ejecutar_etl(lista_envios, lista_clima, alertas_viales)
    print("\n=== Inspección del DataFrame ===")
    inspeccionar_df(df_envios)

    indicadores = indicadores_generales(df_envios)
    print("\n=== Indicadores generales ===")
    print(f"Total de envíos: {indicadores['total_envios']}")
    print(f"Porcentaje de críticos: {indicadores['porcentaje_criticos']:.1f}%")
    print(f"Demora promedio: {indicadores['demora_promedio_horas']:.1f} h")
    print(f"Cumplimiento promedio: {indicadores['cumplimiento_promedio']:.1f}%")
    print("\n=== Porcentaje de envíos críticos por zona ===")
    print(porcentaje_criticos_por_zona(df_envios))
    print("\n=== Demora promedio por zona (horas) ===")
    print(demora_promedio_por_zona(df_envios))

    print("\nSe muestra el gráfico de estados. Al cerrar la ventana termina el programa")
    graficar_estados(df_envios)

if __name__ == "__main__":
    ejecutar_plataforma()