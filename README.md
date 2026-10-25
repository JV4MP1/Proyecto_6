# Plataforma logística de seguimiento de envíos

## ¿De qué trata el proyecto?

El proyecto consiste en desarrollar una plataforma para hacer un seguimiento de distintos envíos y poder detectar posibles demoras.

La idea es juntar información de los envíos con datos de clima y novedades de tránsito. Con esos datos se puede analizar la situación de cada envío y determinar si está en término, tiene algún riesgo de demora, está demorado o se encuentra en estado crítico.

Además, el sistema calcula algunos indicadores, como el porcentaje de envíos críticos por zona o la demora promedio, y muestra un gráfico con los estados de los envíos.

## ¿Cómo está organizado?

El proyecto está dividido en varios archivos, donde cada uno se encarga de una parte diferente:

```text
Proyecto_6/
│
├── main.py
├── config.py
├── claves.py
├── claves_ejemplo.py
├── datos/
│   └── envios_muestra.json
│
├── modulos/
│   ├── envios.py
│   ├── apis.py
│   ├── scraping.py
│   ├── metricas.py
│   ├── etl.py
│   └── notificaciones.py
│
└── README.md
```

`main.py` es el programa principal. Junta las demás partes y ejecuta todo el proceso.

`config.py` tiene las configuraciones y constantes generales que se usan en el proyecto, como las listas, los diccionarios, los umbrales y las direcciones de las APIs.

`claves.py` guarda la API key de OpenWeatherMap. Este archivo no se sube a GitHub. `claves_ejemplo.py` es un modelo para crearlo.

`envios_muestra.json` contiene algunos datos de ejemplo de los envíos para poder probar el funcionamiento del programa.

`envios.py` se utiliza para limpiar los datos de los envíos, hacer los cálculos, clasificar los estados y armar los mensajes para los clientes.

`apis.py` se utiliza para consultar el clima mediante las APIs de Open-Meteo y OpenWeatherMap, y para enviar alertas con el método POST.

`scraping.py` se encarga de obtener las novedades de tránsito de una página web mediante scraping.

`metricas.py` calcula los indicadores con Pandas y genera el gráfico de estados.

`etl.py` realiza la extracción, la unión y la exportación de los datos con Pandas. Esta parte está a cargo del Integrante 1 y todavía está en desarrollo.

`notificaciones.py` se ocupará del envío de emails. Todavía está pendiente.

## Datos de prueba

Para las pruebas se utiliza el archivo `datos/envios_muestra.json`.

El archivo contiene 15 envíos con datos ficticios, como el código de seguimiento, cliente, email, destino, dirección, horas estimadas, horas transcurridas y fecha de despacho.

Algunos datos están mal cargados a propósito para probar la limpieza: espacios de más, mayúsculas mezcladas, emails inválidos o vacíos, una ciudad que no existe (Narnia), una dirección nula, horas nulas y fechas en distintos formatos.

De los 15 envíos se cargan 12. Los otros 3 se rechazan porque tienen un código repetido, les falta el email o tienen las horas escritas como texto. Cuando un email es inválido, el envío no se borra: queda marcado como email no válido y a ese cliente no se le avisa.

## Estados de los envíos

Los envíos se clasifican en cuatro estados:

**En término:** el envío está dentro del tiempo esperado.

**Preventivo:** no hay demora, pero existe alguna situación que podría generarla, como lluvia fuerte o una alerta vial.

**Demorado:** el envío ya presenta una demora de menos de 24 horas.

**Crítico:** el envío tiene una demora de 24 horas o más, o coinciden lluvia fuerte y una alerta vial.

## ¿Cómo se calculan los datos?

**Demora:** es la diferencia entre las horas transcurridas y las horas estimadas. Nunca es menor que 0.

**Porcentaje de cumplimiento:** se calcula como horas estimadas dividido horas transcurridas, por 100, con un máximo de 100. Por ejemplo, si se estimaban 48 horas y pasaron 80, el cumplimiento es del 60 %.

**Distancia simulada:** son kilómetros aproximados desde Buenos Aires hasta cada ciudad. Los valores están guardados en un diccionario de `config.py`.

**Prioridad:** es Alta si la demora llega a 24 horas, Media si hay alguna demora o la distancia es de 1000 km o más, y Baja en los demás casos.

**Lluvia fuerte:** se considera cuando el código de clima indica lluvia fuerte o tormenta, o cuando la precipitación llega a 7,6 mm.

Las noticias de tránsito son de la Ciudad de Buenos Aires, así que si hay una alerta solo se marcan los envíos de la zona AMBA. Los demás se evalúan por demora y clima.

## API de clima

El proyecto utiliza dos APIs públicas para obtener información relacionada con el clima.

**Open-Meteo** no necesita clave y es la fuente principal. Se consulta con el método GET a `https://api.open-meteo.com/v1/forecast`, indicando la latitud y la longitud de cada ciudad. Devuelve la temperatura, la precipitación y un código de clima en formato JSON.

**OpenWeatherMap** necesita una API key. Se usa como segunda fuente y solo se consulta si la clave está configurada.

Para realizar las consultas se utiliza la librería `requests`, con un tiempo máximo de espera y control de los códigos de estado.

La API key no está escrita en el código. Se guarda en `claves.py`, un archivo que está en `.gitignore` y no se sube a GitHub.

Además, cada envío crítico se informa con una alerta enviada por POST a JSONPlaceholder, un servicio de pruebas. En esa alerta no se incluye el nombre ni el email del cliente.

## Web scraping

También se utiliza scraping para obtener las novedades de tránsito del portal de noticias de Infraestructura del Gobierno de la Ciudad de Buenos Aires.

Para esto se utilizan `requests` y `BeautifulSoup`. El programa busca las tarjetas de noticias y se queda con las que pertenecen a la categoría "Cortes de tránsito", guardando el título, la fecha y el enlace de cada una.

Antes de descargar la página, el código lee el `robots.txt` del sitio y verifica que la ruta esté permitida. Como límite de frecuencia, se descarga una sola página por ejecución.

El contenido del portal tiene licencia Creative Commons Reconocimiento 2.5 Argentina.

## Proceso ETL

Los datos utilizados por el sistema vienen de tres lugares: el archivo JSON de envíos, la API de clima y la página web de noticias.

Primero se extraen los datos. Las funciones de `apis.py` y `scraping.py` devuelven listas de diccionarios con las mismas claves, de modo que se pueden convertir directamente en un DataFrame de Pandas.

Después se limpian y transforman: se normalizan los códigos, nombres, destinos, emails y direcciones, se calculan la demora, el cumplimiento, la distancia y la prioridad, y se clasifica cada envío según la demora, el clima y las alertas.

Finalmente se arma el DataFrame de envíos, se revisa su forma, sus tipos de datos y sus valores nulos, y se calculan los indicadores con `groupby`: el porcentaje de envíos críticos por zona y la demora promedio por zona.

Algunas tareas del proceso están a cargo del Integrante 1 en `etl.py`: leer el JSON con Pandas, convertir las fechas, tratar los valores nulos, unir los envíos con los datos del clima con `merge` (la columna en común es `destino`) y exportar el reporte de envíos críticos a CSV o Excel. Cuando ese módulo esté listo, en `main.py` la línea que arma el DataFrame se reemplazará por su función.

## Reporte y gráfico

El programa muestra por pantalla un reporte con los envíos críticos, indicando el cliente, la zona, la causa y la acción recomendada.

También muestra un gráfico de barras, hecho con `df.plot`, con la cantidad de envíos de cada estado. Hay que cerrar la ventana del gráfico para que el programa termine.

## Envío de emails

Los mensajes para los clientes se arman a partir de una plantilla según el estado del envío, por ejemplo "tu envío está demorado". El asunto incluye el código de seguimiento y el estado.

El envío real de los emails con `smtplib` y `EmailMessage` todavía está pendiente en `notificaciones.py`.

## Configuración

Las configuraciones generales del proyecto se encuentran en `config.py`.

De esta manera, si hay que cambiar algún valor utilizado por varios módulos, como los umbrales de demora, las ciudades o las direcciones de las APIs, se puede modificar desde un solo lugar.

La API key se guarda aparte, en `claves.py`.

## Instalación

Para ejecutar el proyecto se necesita tener Python instalado.

Las librerías utilizadas son:

```text
requests
beautifulsoup4
pandas
matplotlib
```

Se pueden instalar con el siguiente comando:

```text
pip install requests beautifulsoup4 pandas matplotlib
```

Para usar OpenWeatherMap hay que copiar `claves_ejemplo.py` con el nombre `claves.py` y escribir adentro la API key propia. Si ese archivo no existe, el programa funciona igual y usa solo Open-Meteo.

## Ejecución

El proyecto debe ejecutarse desde su carpeta principal:

```text
python main.py
```

También se puede probar cada módulo por separado, por ejemplo `python modulos/envios.py`, `python modulos/apis.py`, `python modulos/scraping.py` o `python modulos/metricas.py`. Las pruebas de `apis.py` y `scraping.py` necesitan conexión a internet.

## Objetivo final

La idea es que la plataforma pueda juntar toda la información relacionada con los envíos y utilizarla para detectar posibles problemas.

De esta manera se pueden identificar los envíos que necesitan mayor atención, generar un reporte y, cuando corresponda, avisar al cliente.

El proyecto integra varios de los temas vistos durante la cursada, como Python, JSON, APIs, HTTP, scraping, Pandas, ETL y envío de emails.