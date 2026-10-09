import json
import sys

sys.path.append(".")

from config import RUTA_ENVIO_DATOS, TIMEOUT_SEGUNDOS, URL_CLIMA, URL_TRAFICO, API_KEY_CLIMA
from modulos.apis import consultar_clima_ciudad
from modulos.envios import crear_envio, evaluar_riesgo_envio
from modulos.scraping import analizar_alertas_viales



def ejecutar_plataforma():
    # Scraping de alertas viales
    alertas_viales = analizar_alertas_viales(URL_TRAFICO)

    # Carga de envíos desde JSON
    lista_envios = []
    try:
        with open(RUTA_ENVIO_DATOS, "r", encoding="utf-8") as archivo:
            datos_json = json.load(archivo)
            for item in datos_json:
                envio = crear_envio(
                    item["id"], item["cliente"], item["destino"], item["email"]
                )
                lista_envios.append(envio)
    except FileNotFoundError:
        print(f"No se encontró el archivo en: {RUTA_ENVIO_DATOS}")
        return

    # Integración y Ejecución definitiva
    for envio in lista_envios:
        print(f"- Envio ID {envio['id']} de {envio['cliente']}:")

        # Consultamos el clima mediante la API
        datos_clima = consultar_clima_ciudad(envio["destino"], API_KEY_CLIMA)

        if datos_clima and "rain" in datos_clima.get("clima_principal", "").lower():
            envio["riesgo_clima"] = "Lluvia Fuerte"
        elif datos_clima:
            envio["riesgo_clima"] = (
                f"{datos_clima['descripcion'].title()} ({datos_clima['temperatura']}°C)"
            )

        # Evaluamos riesgo tanto de Clima como de Alerta Vial
        evaluar_riesgo_envio(envio, alertas_viales)

        print(f"  • Destino: {envio['destino']}")
        print(f"  • Clima: {envio['riesgo_clima']}")
        print(f"  • Estado Evaluado: {envio['estado']}")
        print("-" * 50)


if __name__ == "__main__":
    ejecutar_plataforma()