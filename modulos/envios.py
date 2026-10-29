import sys
sys.path.append(".")

import json
from config import (CIUDADES, CENTROS_DISTRIBUCION, PLANTILLAS_MENSAJE, ACCIONES_RECOMENDADAS,
                    HORAS_DEMORA_CRITICA, DISTANCIA_LARGA_KM, RUTA_ENVIO_DATOS)

# N04 y N07
def normalizar_texto(texto):
    if type(texto) != str or texto.strip() == "":
        return "Sin Dato"
    return texto.strip().title()

# N04
def normalizar_id(id_envio):
    return id_envio.strip().upper()

# N04
def limpiar_email(email):
    if type(email) != str:
        return ""
    return email.strip().lower()

# N04
def validar_email(email):
    arroba = email.find("@")
    if arroba <= 0 or " " in email:
        return False
    if email.find("@", arroba + 1) != -1:  # hay una segunda @
        return False
    dominio = email[arroba + 1:]
    if "." not in dominio or dominio[0] == "." or dominio[-1] == ".":
        return False
    return True

# N07
def limpiar_direccion(direccion):
    if type(direccion) != str or direccion.strip() == "":
        return "Sin Dato"
    texto = direccion.strip().title()
    while "  " in texto:
        texto = texto.replace("  ", " ")
    return texto.replace("Cp", "CP")

# N07
def extraer_codigo_postal(direccion):
    if type(direccion) != str:
        return "Sin Dato"
    texto = direccion.upper().replace(":", " ").replace(".", "")
    posicion = texto.find("CP")
    if posicion == -1:
        return "Sin Dato"
    candidato = texto[posicion + 2:].strip()[:4]
    try:
        int(candidato)
    except ValueError:
        return "Sin Dato"
    if len(candidato) != 4:
        return "Sin Dato"
    return candidato

# N02
def calcular_demora_horas(horas_estimadas, horas_transcurridas):
    if horas_estimadas is None or horas_transcurridas is None:
        return None
    demora = horas_transcurridas - horas_estimadas
    if demora < 0:
        demora = 0
    return demora

# N02
def calcular_porcentaje_cumplimiento(horas_estimadas, horas_transcurridas):
    if horas_estimadas is None or horas_transcurridas is None:
        return None
    if horas_transcurridas <= horas_estimadas:
        return 100.0
    return horas_estimadas / horas_transcurridas * 100

# N02
def calcular_distancia_simulada(destino):
    if destino in CIUDADES:
        return CIUDADES[destino]["distancia_km"]
    return None

# N02
def calcular_prioridad(distancia_km, demora_horas):
    if demora_horas is None:
        demora_horas = 0
    if distancia_km is None:
        distancia_km = 0
    if demora_horas >= HORAS_DEMORA_CRITICA:
        return "Alta"
    elif demora_horas > 0 or distancia_km >= DISTANCIA_LARGA_KM:
        return "Media"
    return "Baja"

# N03
def clasificar_estado(demora_horas, lluvia_fuerte, alerta_vial):
    if demora_horas is None:
        demora_horas = 0
    if demora_horas >= HORAS_DEMORA_CRITICA or (lluvia_fuerte and alerta_vial):
        return "Crítico"
    elif demora_horas > 0:
        return "Demorado"
    elif lluvia_fuerte or alerta_vial:
        return "Preventivo"
    return "En término"

def determinar_causa(demora_horas, lluvia_fuerte, alerta_vial):
    causas = []
    if demora_horas is not None and demora_horas > 0:
        causas.append(f"Demora de {demora_horas} h")
    if lluvia_fuerte:
        causas.append("Lluvia fuerte")
    if alerta_vial:
        causas.append("Alerta vial")
    if len(causas) == 0:
        return "Sin causa"
    return " + ".join(causas)

# N03
def evaluar_riesgo_envio(envio, alertas_viales=None):
    if alertas_viales:
        envio["alerta_vial"] = True
    lluvia_fuerte = envio["riesgo_clima"] == "Lluvia Fuerte"
    envio["estado"] = clasificar_estado(envio["demora_horas"], lluvia_fuerte, envio["alerta_vial"])
    envio["causa"] = determinar_causa(envio["demora_horas"], lluvia_fuerte, envio["alerta_vial"])
    envio["accion_recomendada"] = ACCIONES_RECOMENDADAS[envio["estado"]]
    return envio["estado"]

# N04, N05 y N06
def crear_envio(id_envio, cliente, destino, email, horas_estimadas=0, horas_transcurridas=0,
                direccion=None, fecha_despacho=None):
    destino = normalizar_texto(destino)
    email = limpiar_email(email)
    distancia = calcular_distancia_simulada(destino)
    demora = calcular_demora_horas(horas_estimadas, horas_transcurridas)
    zona = "Sin Dato"
    if destino in CIUDADES:
        zona = CIUDADES[destino]["zona"]
    envio = {
        "id": normalizar_id(id_envio),
        "cliente": normalizar_texto(cliente),
        "destino": destino,
        "email": email,
        "email_valido": validar_email(email),
        "direccion": limpiar_direccion(direccion),
        "codigo_postal": extraer_codigo_postal(direccion),
        "fecha_despacho": fecha_despacho,
        "origen": CENTROS_DISTRIBUCION[0],
        "zona": zona,
        "distancia_km": distancia,
        "horas_estimadas": horas_estimadas,
        "horas_transcurridas": horas_transcurridas,
        "demora_horas": demora,
        "cumplimiento": calcular_porcentaje_cumplimiento(horas_estimadas, horas_transcurridas),
        "prioridad": calcular_prioridad(distancia, demora),
        "riesgo_clima": "Sin Evaluar",
        "alerta_vial": False,
    }
    evaluar_riesgo_envio(envio)
    return envio

# N07
def armar_asunto_email(envio):
    return f"Seguimiento de tu envío {envio['id']}: {envio['estado'].upper()}"

# N04 y N06
def generar_mensaje_cliente(envio):
    plantilla = PLANTILLAS_MENSAJE[envio["estado"]]
    return plantilla.format(cliente=envio["cliente"], id=envio["id"], destino=envio["destino"])

# N05
def agregar_envio(lista_envios, envio):
    for existente in lista_envios:
        if existente["id"] == envio["id"]:
            print(f"El envío {envio['id']} ya existe, no se agrega de nuevo")
            return
    lista_envios.append(envio)

# N05
def filtrar_por_estado(lista_envios, estado):
    filtrados = []
    for envio in lista_envios:
        if envio["estado"] == estado:
            filtrados.append(envio)
    return filtrados

# N05
def horas_validas(horas):
    if horas is None:
        return True
    return (type(horas) == int or type(horas) == float) and horas >= 0

# N05
def cargar_envios(ruta=RUTA_ENVIO_DATOS):
    lista_envios = []
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            datos_json = json.load(archivo)
    except FileNotFoundError:
        print(f"No se encontró el archivo en: {ruta}")
        return lista_envios

    numero = 0
    for item in datos_json:
        numero += 1
        if type(item) != dict:
            print(f"Registro {numero} rechazado: no es un objeto JSON")
            continue
        faltantes = []
        for campo in ["id", "cliente", "destino", "email"]:
            if campo not in item:
                faltantes.append(campo)
        if len(faltantes) > 0:
            print(f"Registro {numero} rechazado: faltan los campos {faltantes}")
            continue
        if type(item["id"]) != str or item["id"].strip() == "":
            print(f"Registro {numero} rechazado: el id tiene que ser un texto")
            continue
        estimadas = item.get("horas_estimadas", 0)
        transcurridas = item.get("horas_transcurridas", 0)
        if not horas_validas(estimadas) or not horas_validas(transcurridas):
            print(f"Registro {numero} rechazado: las horas tienen que ser números positivos")
            continue
        envio = crear_envio(item["id"], item["cliente"], item["destino"], item["email"],
                            estimadas, transcurridas, item.get("direccion"), item.get("fecha_despacho"))
        agregar_envio(lista_envios, envio)
    return lista_envios

if __name__ == "__main__":
    envio_test = crear_envio(" env-010 ", " lionel MeSSi ", " santa fe ", "MeSSI@GMAIL.COM ",
                             48, 80, "  bv.   gálvez 1234,  santa fe   CP 3000 ", "2026-10-08")
    print(envio_test)
    envio_test["alerta_vial"] = True
    envio_test["riesgo_clima"] = "Lluvia Fuerte"
    print("Estado con lluvia y alerta:", evaluar_riesgo_envio(envio_test))
    print(armar_asunto_email(envio_test))
    print(generar_mensaje_cliente(envio_test))