import requests

#estos son los valores fijos que no cambian, por eso van en mayusculas y afuera de la funcion
URL_CLIMA = "https://api.openweathermap.org/data/2.5/weather"
TIMEOUT_SEGUNDOS = 10

def consultar_clima_ciudad(ciudad, api_key):
    #este es el formulario que le vamos a mandar a la API
    parametros = {
        "q": ciudad, 
        "appid": api_key,
        "units": "metric", #para que la temperatura venga en grados celsius y no en kelvin
        "lang": "es" #para que la descripcion venga en español 
    }
    
    try:
        #esta linea es la que sale a internet a pedir los datos
        respuesta = requests.get (URL_CLIMA, params=parametros, timeout=TIMEOUT_SEGUNDOS)
    except requests.exceptions.RequestException as error:
        #esto salta si falla la conexion antes de recibir cualquier dato
        print ("No se pudo conectar:", error)
        return None
    
    #200 es el unico codigo que significa que salio bien 
    if respuesta.status_code != 200:
        #si llegas aca es porque algo salio mal, te tenes que fijar que fue 
        if respuesta.status_code == 401:
            print("API Key invalida o todavia no activada")
        elif respuesta.status_code == 404:
            print("No se encontro la ciudad:", ciudad)
        elif respuesta.status_code == 429:
            print("Se alcanzo el limite de solicitudes, esperar y reintentar")
        else:
            print("Error:", respuesta.status_code)
        return None #no tiene sentido seguir si no llegan datos
    
    #a partir de aca, la respuesta vino bien 
    datos = respuesta.json()
    return {
        "temperatura": datos["main"]["temp"],
        "clima_principal": datos["weather"][0]["main"], #weather es una lista, por eso [0] (el primer y unico elemnto)
        "descripcion": datos["weather"][0]["description"]
    }

if __name__ == "__main__":
    #este bloque sirve para probar la funcion sola 
    MI_API_KEY = "964e142c29f9d45b30f5fc112cb8c589"
    resultado = consultar_clima_ciudad("Buenos Aires", MI_API_KEY)
    print(resultado)