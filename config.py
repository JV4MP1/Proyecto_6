# Configuración general del proyecto
# Plataforma logística de seguimiento de envíos

# Configuración de la API de clima
API_TIMEOUT = 10

# Configuración del servidor SMTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# Estados posibles de los envíos
ESTADO_EN_TERMINO = "en término"
ESTADO_PREVENTIVO = "preventivo"
ESTADO_DEMORADO = "demorado"
ESTADO_CRITICO = "crítico"

# Niveles de prioridad
PRIORIDAD_NORMAL = "normal"
PRIORIDAD_MEDIA = "media"
PRIORIDAD_ALTA = "alta"
PRIORIDAD_CRITICA = "crítica"

# Archivos de datos
ARCHIVO_ENVIOS = "datos/envios_muestra.json"

# Configuración de reportes
ARCHIVO_REPORTE = "reportes/envios_criticos.csv"

# Configuración general de scraping
SCRAPING_TIMEOUT = 10
SCRAPING_DELAY = 2
