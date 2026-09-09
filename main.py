from modulos.envios import crear_envio, evaluar_riesgo_envio

def ejecutar_plataforma():
    #Creamos la lista que almacenará los envios creados y tambien agregamos envios iniciales
    lista_envios = []
    lista_envios.append(crear_envio("env-010", "lionel MeSSi", "santa fe", "LionelMeSSI@GMAIL.COM"))
    lista_envios.append(crear_envio("env-007", "Cristiano Ronaldo", "Tierra del Fuego", "  comandante@gmail.com"))
    lista_envios.append(crear_envio("env-006", "lebron James", "  Formosa", "lebroncito@gmail.COM"))
    #Iteramos la lista para mostrar todos los envios almacenados y sus datos correspondientes
    for envio in lista_envios:
        print(f"Envio con el ID {envio["id"]} creado: ")
        print(f"- Cliente: {envio["cliente"]}")
        print(f"- Destino: {envio["destino"]}")
        print(f"- Estado Actual: {envio["estado"]}")
        print("-"*50)

if __name__ == "__main__":
    ejecutar_plataforma()