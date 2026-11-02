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
├── salidas/   (la genera el programa con los reportes y el registro de correos, no se sube a GitHub)
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

`envios.py` se utiliza para limpiar los datos de los envíos, hacer los cálculos, clasificar los estados y armar los mensajes para los clientes (incisos N02 a N07).

`apis.py` se utiliza para consultar el clima mediante las APIs de Open-Meteo y OpenWeatherMap, y para enviar alertas con el método POST (incisos N13 a N18).

`scraping.py` se encarga de obtener las novedades de tránsito de una página web mediante scraping (incisos N08 a N12).

`metricas.py` calcula los indicadores con Pandas y genera el gráfico de estados (incisos N20 y N23).

`etl.py` realiza la extracción, la transformación, la unión y la exportación de los datos con Pandas (incisos N19 a N23).

`notificaciones.py` se encarga de enviar el reporte diario y los avisos a los clientes por email, y de guardar un registro de cada correo enviado (incisos N24 y N25).

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

El proceso está en `modulos/etl.py` y lo ejecuta `main.py` con la función `ejecutar_etl`, después de evaluar los riesgos de cada envío. Devuelve el DataFrame que usa `metricas.py` y las rutas de los archivos generados, para que `notificaciones.py` pueda adjuntar el reporte.

**Extracción.** Entran tres listas de diccionarios: los envíos (`envios.py`), el clima (`apis.py`) y las alertas viales (`scraping.py`). Se convierten en DataFrames y se conserva una copia cruda de los envíos, que se usa para validar que la transformación no perdió filas. También se lee `envios_muestra.json` con `read_json` para comparar sus 15 filas con las 12 cargadas. La limpieza y la clasificación no se repiten: siguen en `envios.py`.

**Transformación.**

- **Fechas:** `fecha_despacho` trae dos formatos, así que cada uno se convierte por separado con `format=` y después se combinan con `fillna`. Convertir todo junto pierde fechas o invierte el día y el mes sin avisar. Lo que no es una fecha queda como `NaT` y no se inventa. Con la muestra quedan 10 fechas válidas y 2 `NaT`.
- **Nulos:** no se imputan. Una demora de 0 afirmaría que el envío llegó en tiempo cuando no se sabe, y bajaría el promedio. Los envíos sin horas o con un destino desconocido se marcan en `datos_incompletos` y las fechas faltantes en `fecha_invalida`.
- **Columnas calculadas:** `severidad` sale de aplicar `ESTADOS_ENVIO` con `.map()`, y `diferencia_horas` de una resta entre columnas.
- **Clima:** `merge` por `destino` con `how="left"`, para conservar todos los envíos, y `validate="many_to_one"`. Sin dato de clima no significa que no llueva, por eso `lluvia_fuerte` queda nula y se marca `clima_disponible`.
- **Alertas:** no tienen una clave por envío y unirlas directo multiplicaría las filas. Primero se resumen con `groupby` a una fila por zona y después se unen por `zona`. Fuera de AMBA quedan nulas, porque las noticias son solo de la Ciudad de Buenos Aires.
- **Resúmenes:** envíos por estado y zona, envíos por día de despacho y una tabla por zona armada con `join`.

**Carga.** Todo se escribe en la carpeta `salidas/`, nunca en `datos/`. `AAAA-MM-DD` es la fecha de la ejecución.

| Archivo | Contenido |
|---|---|
| `reporte_criticos_AAAA-MM-DD` (`.csv`, `.xlsx`, `.json`, `.csv.gz`) | Reporte diario de críticos con cliente, zona, causa y acción recomendada |
| `revision_datos_AAAA-MM-DD.csv` | Envíos con datos incompletos, para que alguien los revise |
| `comparacion_criticos_AAAA-MM-DD.csv` | Críticos nuevos, resueltos y persistentes contra el reporte anterior. No se genera el primer día |
| `historial_criticos.csv` | Todos los reportes diarios apilados con `concat` |
| `ranking_criticos_AAAA-MM-DD.png` | Gráfico de zonas según el porcentaje de críticos |

**Validaciones.** Con `assert` se controla que los `id` sean únicos y no nulos, que cada `merge` mantenga la cantidad de filas y que estén las columnas que necesita `metricas.py`. Después de exportar, cada archivo del reporte se vuelve a leer, incluido el comprimido, y se comparan sus filas, columnas e `id`. Si una regla no se cumple, el programa se detiene e informa cuál fue.

## Reporte y gráfico

El programa muestra por pantalla un reporte con los envíos críticos, indicando el cliente, la zona, la causa y la acción recomendada, y lo exporta como archivo en `salidas/`.

También muestra un gráfico de barras, hecho con `df.plot`, con la cantidad de envíos de cada estado. Hay que cerrar la ventana del gráfico para que el programa termine. El ranking de zonas no se abre en una ventana: se guarda como imagen en `salidas/`.

## Envío de emails

El módulo `notificaciones.py` envía dos tipos de correos con `smtplib` y `EmailMessage`.

El primero es el **reporte diario de envíos críticos**. Se manda a la lista de destinatarios (`DESTINATARIOS_REPORTE`) con el listado de los envíos críticos en el cuerpo (cliente, zona, causa y acción recomendada) y tres archivos adjuntos: el reporte en CSV, el reporte en Excel y el gráfico de zonas. Los adjuntos salen de las rutas que devuelve el ETL y su lista está en `ADJUNTOS_REPORTE`, dentro de `config.py`.

El segundo son los **avisos a los clientes**: un correo por cada envío que no está en término, con el asunto y el mensaje que se arman en `envios.py` según el estado. Si el email del cliente no es válido, no se envía y queda anotado como omitido.

Mientras `MODO_PRUEBA` esté en `True` (es el valor por defecto), los avisos no se mandan a los clientes de la muestra: se envían a los destinatarios del reporte y el asunto empieza con "[PRUEBA para ...]". Para escribirle a los clientes de verdad hay que cambiarlo a `False` en `config.py`.

La conexión se hace una sola vez y sigue los pasos de la clase: conectarse al servidor con `smtplib.SMTP`, `ehlo()`, `starttls()` para cifrar, `ehlo()`, `login()` y un `send_message()` por cada correo.

**Trazabilidad de errores.** Cada correo queda registrado en `salidas/log_correos_AAAA-MM-DD.csv` con la fecha y la hora, los destinatarios, el asunto, los adjuntos, el resultado (Enviado, Error u Omitido) y el detalle del error. Se controlan estos casos:

**Contraseña rechazada:** `login()` tira `SMTPAuthenticationError` y todos los correos pendientes quedan como error.

**Correo rechazado por el servidor:** `send_message()` tira una excepción de `smtplib` y solo ese correo queda como error. Los demás se siguen enviando.

**Sin conexión o servidor que no responde:** se captura `OSError` y los correos que faltaban quedan como error. Si la conexión se cae a mitad de camino, los que ya salieron figuran como enviados.

En ningún caso el programa se detiene. Si en `claves.py` faltan los datos del correo, el programa avisa y no envía nada.

## Otros puntos de la consigna

**API pública y API privada (N13).** Una API pública la puede usar cualquier desarrollador siguiendo las condiciones que publica el servicio, y a veces pide registrarse o usar una clave. Una API privada o interna solo la usan usuarios o aplicaciones autorizadas, por ejemplo el sistema interno de una empresa. Open-Meteo es pública y no pide clave, y OpenWeatherMap es pública pero necesita una API key. El proyecto solo usa APIs públicas.

**JSON y XML (N14).** Las APIs del proyecto responden en JSON, que `requests` convierte en un diccionario con `respuesta.json()`. Después se accede a los datos con claves y posiciones, y los números ya vienen como números. XML organiza los datos en etiquetas anidadas, parecido a HTML, y se recorre con una librería de XML. Todos sus valores llegan como texto y hay que convertirlos. El proyecto no consume XML.

**Métodos HTTP (N15).** Se usa GET para consultar el clima y descargar páginas, y POST para enviar la alerta de un envío crítico. PUT serviría para reemplazar todos los datos de un envío, PATCH para cambiar solo una parte, por ejemplo el estado, y DELETE para eliminar un envío. No se usan porque el proyecto no tiene una API propia que guarde los envíos.

**HTML de la página (N09).** Con las herramientas del navegador (F12) se vio que cada noticia es una etiqueta `a` con la clase `card` y un `href`. Adentro tiene una `img` con la clase `card-img-top`, un `div` con la clase `card-body` que contiene el título en un `h4` con la clase `card-title` y un texto en un `p` con la clase `card-text`, y un `div` con la clase `card-footer`. Las tarjetas están dentro de un `div` con la clase `card-deck`. El título de la página está en la etiqueta `title`, dentro de `head`.

**DNS e IP (N08).** El DNS traduce el nombre de un sitio a su dirección IP. Las IP de los tres sitios se consultaron con `nslookup` el 25/10/2026 y están en `SITIOS_WEB`, dentro de `config.py`. Pueden cambiar con el tiempo.

**Protocolos de correo (N25).** SMTP es el protocolo que se usa para enviar un correo, desde el cliente hasta el servidor y entre servidores. No sirve para leer el buzón: eso lo resuelven POP3 e IMAP. POP3 descarga los mensajes al dispositivo y normalmente los borra del servidor, así que quedan en un solo equipo, y no maneja carpetas ni estados en el servidor. IMAP deja los mensajes en el servidor y los sincroniza entre varios dispositivos, con carpetas y marcas como leído. Como el proyecto solo envía correos, usa SMTP, con `smtplib` para la conexión y `EmailMessage` para armar el mensaje.

**Servidor de email usado.** Gmail, con `smtp.gmail.com` y el puerto 587. La conexión empieza sin cifrar y se pasa a una conexión cifrada con `starttls()` antes de enviar la contraseña.

**Acceso a Gmail desde Python.** Gmail ya no acepta la contraseña normal de la cuenta para un programa. Hay dos formas de entrar. La primera es una contraseña de aplicación: se genera en la cuenta de Google, hace falta tener activada la verificación en dos pasos y se usa en lugar de la contraseña. La segunda es OAuth, donde el usuario autoriza a la aplicación y esta recibe un token, sin manejar nunca la contraseña. El proyecto usa la contraseña de aplicación, guardada en `claves.py`. Si es incorrecta, `login()` tira `SMTPAuthenticationError` y el error queda en el registro de correos.

## Configuración

Las configuraciones generales del proyecto se encuentran en `config.py`.

De esta manera, si hay que cambiar algún valor utilizado por varios módulos, como los umbrales de demora, las ciudades o las direcciones de las APIs, se puede modificar desde un solo lugar.

La API key y los datos del correo se guardan aparte, en `claves.py`. Los datos del correo son el usuario, la contraseña de aplicación y los destinatarios del reporte.

## Instalación

Para ejecutar el proyecto se necesita tener Python instalado.

Las librerías utilizadas son:

```text
requests
beautifulsoup4
pandas
matplotlib
openpyxl
```

Se pueden instalar con el siguiente comando:

```text
pip install requests beautifulsoup4 pandas matplotlib openpyxl
```

Hay que copiar `claves_ejemplo.py` con el nombre `claves.py` y completar los datos propios: la API key de OpenWeatherMap y los datos del correo. Si ese archivo no existe, el programa funciona igual: usa solo Open-Meteo y no envía emails.

## Ejecución

El proyecto debe ejecutarse desde su carpeta principal:

```text
python main.py
```

También se puede probar cada módulo por separado, por ejemplo `python modulos/envios.py`, `python modulos/apis.py`, `python modulos/scraping.py`, `python modulos/metricas.py`, `python modulos/etl.py` o `python modulos/notificaciones.py`. Las pruebas de `apis.py`, `scraping.py` y `notificaciones.py` necesitan conexión a internet. La de `notificaciones.py` también necesita los datos del correo en `claves.py`.

## Objetivo final

La idea es que la plataforma pueda juntar toda la información relacionada con los envíos y utilizarla para detectar posibles problemas.

De esta manera se pueden identificar los envíos que necesitan mayor atención, generar un reporte y, cuando corresponda, avisar al cliente.

El proyecto integra varios de los temas vistos durante la cursada, como Python, JSON, APIs, HTTP, scraping, Pandas, ETL y envío de emails.