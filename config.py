# N17
try:
    from claves import API_KEY_CLIMA
except ImportError:
    API_KEY_CLIMA = ""

# N08
URL_SITIO = "https://buenosaires.gob.ar"
RUTA_NOTICIAS = "/gcaba_historico/infraestructura/noticias"
URL_TRAFICO = URL_SITIO + RUTA_NOTICIAS
URL_OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
URL_CLIMA = "https://api.openweathermap.org/data/2.5/weather"
URL_ALERTAS_POST = "https://jsonplaceholder.typicode.com/posts"

NAVEGADOR = "Google Chrome"

# N08
SITIOS_WEB = {
    "noticias": {"url": URL_TRAFICO, "dominio": "buenosaires.gob.ar", "ip": "200.16.89.104"},
    "open_meteo": {"url": URL_OPEN_METEO, "dominio": "api.open-meteo.com", "ip": "208.115.249.236"},
    "openweathermap": {"url": URL_CLIMA, "dominio": "api.openweathermap.org", "ip": "169.197.141.2"},
}

RUTA_ENVIO_DATOS = "datos/envios_muestra.json"
TIMEOUT_SEGUNDOS = 10

# N10
USER_AGENT = "TallerProgramacionII-Proyecto6 (uso academico)"
PALABRA_CLAVE_ALERTA = "cortes de tránsito"
ZONA_ALERTAS_VIALES = "AMBA" 

# N05
URLS_NOVEDADES_VIALES = [URL_TRAFICO]
CENTROS_DISTRIBUCION = ["Buenos Aires"]

# N06
ENDPOINTS_API = {"open_meteo": URL_OPEN_METEO, "openweathermap": URL_CLIMA}
TOKENS_API = {"openweathermap": API_KEY_CLIMA}

# N02 y N03
HORAS_DEMORA_CRITICA = 24
DISTANCIA_LARGA_KM = 1000
LLUVIA_FUERTE_MM = 7.6
CODIGOS_LLUVIA_FUERTE = [65, 67, 82, 95, 96, 99]

# N06
ESTADOS_ENVIO = {"En término": 0, "Preventivo": 1, "Demorado": 2, "Crítico": 3}
ESTADO_CRITICO = "Crítico"

# N02 y N06
CIUDADES = {
    "Buenos Aires": {"zona": "AMBA", "distancia_km": 20, "lat": -34.61, "lon": -58.38},
    "Rosario": {"zona": "Centro", "distancia_km": 300, "lat": -32.95, "lon": -60.64},
    "Santa Fe": {"zona": "Centro", "distancia_km": 470, "lat": -31.63, "lon": -60.70},
    "Córdoba": {"zona": "Centro", "distancia_km": 700, "lat": -31.42, "lon": -64.18},
    "Mendoza": {"zona": "Cuyo", "distancia_km": 1050, "lat": -32.89, "lon": -68.84},
    "Tucumán": {"zona": "NOA", "distancia_km": 1300, "lat": -26.82, "lon": -65.22},
    "Salta": {"zona": "NOA", "distancia_km": 1600, "lat": -24.78, "lon": -65.41},
    "Formosa": {"zona": "NEA", "distancia_km": 1300, "lat": -26.19, "lon": -58.18},
    "Bariloche": {"zona": "Patagonia", "distancia_km": 1600, "lat": -41.13, "lon": -71.31},
    "Ushuaia": {"zona": "Patagonia", "distancia_km": 3100, "lat": -54.80, "lon": -68.30},
}

# N06
ACCIONES_RECOMENDADAS = {
    "En término": "No requiere acción",
    "Preventivo": "Monitorear el envío y avisar al cliente de una posible demora",
    "Demorado": "Contactar al cliente y reprogramar la entrega",
    "Crítico": "Escalar al responsable de la zona y contactar al cliente de inmediato",
}
PLANTILLAS_MENSAJE = {
    "En término": "Hola {cliente}, tu envío {id} con destino a {destino} está en término.",
    "Preventivo": "Hola {cliente}, tu envío {id} hacia {destino} podría demorarse por el clima o el tránsito.",
    "Demorado": "Hola {cliente}, tu envío {id} hacia {destino} está demorado. Estamos trabajando para entregarlo.",
    "Crítico": "Hola {cliente}, tu envío {id} hacia {destino} está en estado crítico. Un asesor se va a comunicar con vos.",
}

# N13
DESCRIPCIONES_CLIMA = {
    0: "Cielo despejado", 1: "Mayormente despejado", 2: "Parcialmente nublado", 3: "Nublado",
    45: "Niebla", 51: "Llovizna", 61: "Lluvia ligera", 63: "Lluvia moderada",
    65: "Lluvia fuerte", 80: "Chubascos ligeros", 82: "Chubascos violentos",
    95: "Tormenta eléctrica", 99: "Tormenta con granizo",
}