import sys
sys.path.append(".")

import requests
from config import (URL_CLIMA, URL_OPEN_METEO, URL_ALERTAS_POST, TIMEOUT_SEGUNDOS, API_KEY_CLIMA,
                    CIUDADES, DESCRIPCIONES_CLIMA, LLUVIA_FUERTE_MM, CODIGOS_LLUVIA_FUERTE)

# N16
def avisar_error_http(codigo, que_se_pidio):
    if codigo == 401:
        print("API Key inválida o todavía no activada")
    elif codigo == 404:
        print("No se encontró:", que_se_pidio)
    elif codigo == 429:
        print("Se alcanzó el límite de solicitudes, esperar y reintentar")
    else:
        print("Error", codigo, "al consultar:", que_se_pidio)


# N13, N16 y N18
def consultar_clima_open_meteo(ciudad):
    if ciudad not in CIUDADES:
        print("No tengo las coordenadas de la ciudad:", ciudad)
        return None

    parametros = {
        "latitude": CIUDADES[ciudad]["lat"],
        "longitude": CIUDADES[ciudad]["lon"],
        "current": "temperature_2m,precipitation,weather_code",
        "timezone": "auto",
    }
    try:
        respuesta = requests.get(URL_OPEN_METEO, params=parametros, timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.RequestException as error:
        print("No se pudo conectar con Open-Meteo:", error)
        return None

    if respuesta.status_code != 200:
        avisar_error_http(respuesta.status_code, ciudad)
        return None

    # N14
    actual = respuesta.json()["current"]
    codigo = actual["weather_code"]
    lluvia_fuerte = codigo in CODIGOS_LLUVIA_FUERTE or actual["precipitation"] >= LLUVIA_FUERTE_MM
    return {
        "destino": ciudad,
        "temperatura": actual["temperature_2m"],
        "precipitacion_mm": actual["precipitation"],
        "descripcion": DESCRIPCIONES_CLIMA.get(codigo, "Sin descripción"),
        "lluvia_fuerte": lluvia_fuerte,
    }


# N17
def consultar_clima_ciudad(ciudad, api_key):
    if api_key == "":
        print("Falta configurar la API key en claves.py")
        return None

    parametros = {"q": ciudad + ",AR", "appid": api_key, "units": "metric", "lang": "es"}
    try:
        respuesta = requests.get(URL_CLIMA, params=parametros, timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.RequestException as error:
        print("No se pudo conectar con OpenWeatherMap:", error)
        return None

    if respuesta.status_code != 200:
        avisar_error_http(respuesta.status_code, ciudad)
        return None

    datos = respuesta.json()
    return {
        "destino": ciudad,
        "temperatura": datos["main"]["temp"],
        "descripcion": datos["weather"][0]["description"],
    }

def obtener_clima_destinos(destinos):
    ciudades_consultadas = []
    lista_clima = []
    for ciudad in destinos:
        if ciudad in ciudades_consultadas:
            continue
        ciudades_consultadas.append(ciudad)
        clima = consultar_clima_open_meteo(ciudad)
        if clima is not None:
            lista_clima.append(clima)
    return lista_clima


# N15
def enviar_alerta_post(envio):
    alerta = {
        "id_envio": envio["id"],
        "estado": envio["estado"],
        "zona": envio["zona"],
        "causa": envio["causa"],
        "accion_recomendada": envio["accion_recomendada"],
    }
    try:
        respuesta = requests.post(URL_ALERTAS_POST, json=alerta, timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.RequestException as error:
        print("No se pudo enviar la alerta por POST:", error)
        return None

    if respuesta.status_code != 201:
        avisar_error_http(respuesta.status_code, envio["id"])
        return None
    return respuesta.json()


if __name__ == "__main__":
    print(consultar_clima_open_meteo("Buenos Aires"))
    print(consultar_clima_ciudad("Buenos Aires", API_KEY_CLIMA))