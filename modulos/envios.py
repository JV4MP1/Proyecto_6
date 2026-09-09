def normalizar_texto(texto:str):
    #Se pregunta si la entrada de cadena de texto esta vacía
    if not texto or texto.strip() == "":
        return "Sin Dato"
    #Retornamos el texto limpio de espacios innecesarios y cambiamos las iniciales a mayúsculas
    return texto.strip().title()


def validar_email(email:str):
    #Evitamos que la entrada tenga espacios innecesarios y que el email este en minusculas
    email_limpio = email.strip().lower() 
    #Se pregunta si el email otorgado contiene los caracteres de "@" y "."
    if "@" in email_limpio and "." in email_limpio:
        return email_limpio
    return "email_invalido@dominio.com"
    
def normalizar_id(id_envio:str):
    #Se devuelve el id en mayusculas y evitando que tenga espacios innecesarios
    return id_envio.strip().upper()

def crear_envio(id_envio, cliente, destino, email):
    #Llamamos a las funciones anteriormente creadas para guardar los datos limpios al diccionario
    id_envio = normalizar_id(id_envio)
    cliente = normalizar_texto(cliente)
    destino = normalizar_texto(destino)
    email = validar_email(email)
    #Creamos diccionario con el fin de guardar los datos obtenidos
    envio = {
        "id" : id_envio,
        "cliente" : cliente,
        "destino" : destino,
        "email" : email,
        "estado" : "En Término",
        "riesgo_clima" : "Sin Evaluar",
        "alerta_vial" : False,
    }
    
    return envio

def evaluar_riesgo_envio(envio):
    #Evaluamos los distintos escenarios acorde al pronostico y si hay alerta vial
    if envio.get("riesgo_clima") == "Lluvia Fuerte" and envio.get("alerta_vial") is True:
        envio["estado"] = "Critico"
    elif envio.get("riesgo_clima") == "Lluvia Fuerte" or envio.get("alerta_vial") is True:
        envio["estado"] = "Preventivo"
    else:
        envio["estado"] = "En término"
        
    return envio["estado"]

""" PRUEBA; YA CORRECTAMENTE EVALUADO

if __name__ == "__main__":
    # Test creando un envio con espacios de más, minusculas en iniciales y mayúsculas en mails
    envio_test = crear_envio(" env-010 ", " lionel MeSSi ", " santa fe ", "MeSSI@GMAIL.COM ")
    print(f"Envío creado: {envio_test}")
    
    # Test de prueba para las función de riesgo_envio
    envio_test["alerta_vial"] = True
    envio_test["riesgo_clima"] = "Lluvia Fuerte"
    nuevo_estado = evaluar_riesgo_envio(envio_test)
    print(f"Nuevo estado calculado: {nuevo_estado}")

"""