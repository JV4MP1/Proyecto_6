# Módulo de scraping: alertas viales del portal de noticias del Gobierno de la Ciudad
import sys
sys.path.append(".")

import requests
from bs4 import BeautifulSoup
from config import (URL_SITIO, RUTA_NOTICIAS, URL_TRAFICO, TIMEOUT_SEGUNDOS, USER_AGENT,
                    PALABRA_CLAVE_ALERTA, NAVEGADOR, SITIOS_WEB)


# N10: lee el robots.txt y revisa que la ruta no esté en un Disallow
def puede_scrapear(url_sitio, ruta):
    try:
        respuesta = requests.get(url_sitio + "/robots.txt", headers={"User-Agent": USER_AGENT},
                                 timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.RequestException as error:
        print("No se pudo leer el robots.txt, no se hace scraping:", error)
        return False
    if respuesta.status_code == 404:  # si el sitio no tiene robots.txt no hay restricciones
        return True
    if respuesta.status_code != 200:
        print("No se pudo leer el robots.txt, no se hace scraping. Código:", respuesta.status_code)
        return False

    for linea in respuesta.text.split("\n"):
        if "Disallow:" in linea:
            prohibida = linea.replace("Disallow:", "").strip()
            if prohibida != "" and ruta[:len(prohibida)] == prohibida:
                print("El robots.txt prohíbe esta ruta:", prohibida)
                return False
    return True


# N10 y N16: descarga el HTML con User-Agent y timeout. Es una sola página por ejecución
# (límite de frecuencia: no se hacen pedidos en bucle)
def obtener_html(url):
    if not puede_scrapear(URL_SITIO, RUTA_NOTICIAS):
        return None
    try:
        respuesta = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.RequestException as error:
        print("Error al conectar con el portal:", error)
        return None
    if respuesta.status_code != 200:
        print("El portal respondió con el código", respuesta.status_code)
        return None
    return respuesta.text


# N11: recupera de un elemento su texto, href, clases, id, src y atributos data-*
def extraer_atributos(elemento):
    imagen = elemento.find("img")
    datos = {}
    for nombre in elemento.attrs:
        if nombre[:5] == "data-":
            datos[nombre] = elemento[nombre]
    resultado = {
        "texto": elemento.get_text(" ", strip=True),
        "href": elemento.get("href", "Sin Dato"),  # con .get() no da error si falta el atributo
        "clases": elemento.get("class", []),
        "id": elemento.get("id", "Sin Dato"),
        "src": "Sin Dato",
        "data": datos,
    }
    if imagen is not None:
        resultado["src"] = imagen.get("src", "Sin Dato")
    return resultado


# N08: registra el sitio (URL, dominio, IP y navegador) y toma datos básicos con find
def registrar_sitio(nombre, html=None):
    datos = SITIOS_WEB[nombre]
    sitio = {
        "nombre": nombre,
        "url": datos["url"],
        "dominio": datos["dominio"],
        "ip": datos["ip"],
        "navegador": NAVEGADOR,
        "titulo": "Sin Dato",
        "primera_noticia": "Sin Dato",
    }
    if html is None:
        return sitio

    sopa = BeautifulSoup(html, "html.parser")
    titulo = sopa.find("title")  # find devuelve solo el primer elemento, o None
    if titulo is not None:
        sitio["titulo"] = titulo.get_text(strip=True)
    tarjeta = sopa.find("a", class_="card")
    if tarjeta is not None:
        titulo_noticia = tarjeta.find("h4", class_="card-title")
        if titulo_noticia is not None:
            sitio["primera_noticia"] = titulo_noticia.get_text(strip=True)
    return sitio


# N12: un find_all por cada tipo de criterio. Devuelve cuántos elementos encontró cada uno
def ejemplos_find_all(html):
    sopa = BeautifulSoup(html, "html.parser")
    return {
        "etiqueta": len(sopa.find_all("a")),
        "clase": len(sopa.find_all(class_="card")),
        "id": len(sopa.find_all(id=True)),
        "atributos": len(sopa.find_all("a", attrs={"href": True})),
        "texto": len(sopa.find_all(string="Cortes de tránsito")),
        "lambda": len(sopa.find_all(lambda tag: tag.name == "a" and "card" in tag.get("class", []))),
        "combinado": len(sopa.find_all("a", class_="card", attrs={"href": True}, limit=5)),
    }


# N07: saca la fecha del texto "Fecha de publicación: dd/mm/aaaa"
def extraer_fecha(texto):
    marca = "Fecha de publicación:"
    posicion = texto.find(marca)
    if posicion == -1:
        return "Sin Dato"
    fecha = texto[posicion + len(marca):].strip()[:10]
    return fecha


# N12 y tarea 2.1: find_all combinando etiqueta, clase y atributo, y después filtra por texto
# Devuelve una lista de diccionarios con las mismas claves, lista para pd.DataFrame
def buscar_alertas_viales(html):
    sopa = BeautifulSoup(html, "html.parser")
    alertas = []
    for tarjeta in sopa.find_all("a", class_="card", href=True):
        texto = tarjeta.get_text(" ", strip=True)
        titulo = tarjeta.find("h4", class_="card-title")
        if PALABRA_CLAVE_ALERTA not in texto.lower() or titulo is None:
            continue
        enlace = tarjeta["href"]
        if enlace[:1] == "/":  # el enlace viene sin el dominio
            enlace = URL_SITIO + enlace
        alertas.append({
            "titulo": titulo.get_text(strip=True),
            "fecha": extraer_fecha(texto),
            "enlace": enlace,
        })
    return alertas


if __name__ == "__main__":
    # prueba del módulo solo (necesita internet)
    html_portal = obtener_html(URL_TRAFICO)
    print(registrar_sitio("noticias", html_portal))
    if html_portal is not None:
        print("Criterios de find_all:", ejemplos_find_all(html_portal))
        print("Alertas encontradas:", buscar_alertas_viales(html_portal))