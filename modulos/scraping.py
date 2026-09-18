import requests
from bs4 import BeautifulSoup
import sys
sys.path.append(".")
from config import URL_TRAFICO, TIMEOUT_SEGUNDOS

def analizar_alertas_viales(url: str):
    alertas = []
    
    try:
        # pedir info de la página al servidor
        respuesta = requests.get(url, timeout= TIMEOUT_SEGUNDOS)
        
        # si el servidor respondió OK (200), procesamos el HTML
        if respuesta.status_code == 200:
            #Parseo
            soup = BeautifulSoup(respuesta.text, "html.parser")
            lista_noticias = soup.find_all("a", class_="card") #guardamos las cards de las noticias
            #iteramos la lista de noticias
            for card in lista_noticias:
                if "cortes de tránsito" in card.text.lower(): #extraemos unicamente las noticias que tengas corte de transito como filtro
                    titulo_html = card.find("h4", class_="card-title") #encontramos los titulos de cada alerta vial
                    titulo = titulo_html.get_text(strip=True) #limpiamos el titulo
                    alertas.append(titulo) #agregamos a la lista
                        
    except requests.exceptions.RequestException as error:
        # si falla la conexion, informamos el error sin romper el programa
        print(f"Error al conectar con el servicio de tráfico: {error}")
        
    # devolvemos la lista (con datos o vacía, pero el programa sigue sin romperse)
    return alertas


""" PRUEBA; YA CORRECTAMENTE EVALUADO
if __name__ == "__main__":
    resultado = analizar_alertas_viales(URL_TRAFICO)
    print("Alertas encontradas:", resultado)
"""