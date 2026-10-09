# Plataforma logística de seguimiento de envíos

## ¿De qué trata el proyecto?

El proyecto consiste en desarrollar una plataforma para hacer un seguimiento de distintos envíos y poder detectar posibles demoras.

La idea es juntar información de los envíos con datos de clima y novedades de tránsito. Con esos datos se puede analizar la situación de cada envío y determinar si está en término, tiene algún riesgo de demora, está demorado o se encuentra en estado crítico.

Además, el sistema permite generar reportes y enviar avisos por email cuando sea necesario.

## ¿Cómo está organizado?

El proyecto está dividido en varios archivos, donde cada uno se encarga de una parte diferente:

```text
Proyecto/
│
├── config.py
├── datos/
│   └── envios_muestra.json
│
├── envios.py
├── rutas.py
├── scraping.py
├── api_clima.py
├── etl.py
├── reportes.py
├── correo.py
│
└── README.md
```

`config.py` tiene las configuraciones y constantes generales que se usan en el proyecto.

`envios_muestra.json` contiene algunos datos de ejemplo de los envíos para poder probar el funcionamiento del programa.

`envios.py` se utiliza para trabajar con los envíos y sus estados.

`rutas.py` contiene la información relacionada con las rutas y las zonas.

`scraping.py` se encarga de obtener información de páginas web mediante scraping.

`api_clima.py` se utiliza para consultar información del clima mediante una API.

`etl.py` realiza el proceso de extracción, transformación y carga de los datos.

`reportes.py` genera los reportes con la información procesada.

`correo.py` se ocupa del envío de emails y de los archivos adjuntos.

## Datos de prueba

Para las primeras pruebas se utiliza el archivo `datos/envios_muestra.json`.

El archivo contiene datos ficticios como el código de seguimiento, cliente, email, origen, destino, zona, estado, prioridad y cantidad de horas de demora.

Por ejemplo, un envío puede encontrarse en estado "demorado" y tener una prioridad alta. Esto permite probar cómo funciona el sistema sin tener que utilizar información real.

## Estados de los envíos

Los envíos se pueden clasificar en cuatro estados:

**En término:** el envío está dentro del tiempo esperado.

**Preventivo:** existe alguna situación que podría generar una demora.

**Demorado:** el envío ya presenta una demora.

**Crítico:** el envío presenta una situación que necesita atención prioritaria.

## API de clima

El proyecto utiliza una API pública para obtener información relacionada con el clima.

La información obtenida puede servir para detectar situaciones que podrían afectar una ruta o generar una demora en un envío.

Para realizar las consultas se utiliza la librería `requests`.

Las claves o tokens necesarios para acceder a una API no deben quedar escritos directamente en el código.

## Web scraping

También se utiliza scraping para obtener información de páginas web públicas que puedan aportar novedades relacionadas con el tránsito o las rutas.

Para esto se utilizan `requests` y `BeautifulSoup`.

Antes de realizar el scraping hay que tener en cuenta las condiciones de uso de la página y respetar `robots.txt` y los límites de frecuencia.

## Proceso ETL

Los datos utilizados por el sistema pueden venir de diferentes lugares, por ejemplo del archivo JSON, de una API o de una página web.

Primero se extraen los datos, después se limpian y transforman y finalmente se guardan en un formato que pueda utilizar el resto del proyecto.

Para esta parte se utiliza Pandas.

Algunas de las tareas que se pueden realizar son eliminar datos incorrectos, modificar tipos de datos, trabajar con valores vacíos y combinar información de diferentes fuentes.

## Reportes

Uno de los objetivos del proyecto es generar un reporte con los envíos que presentan una situación crítica.

El reporte debe mostrar información útil para poder tomar una decisión, como el cliente, la zona, la causa de la demora y una posible acción a realizar.

Los datos procesados pueden guardarse en archivos como CSV, Excel o JSON.

## Envío de emails

Cuando un envío necesita ser informado, el sistema puede generar un email para el cliente.

El correo puede incluir información del envío y, cuando corresponda, archivos adjuntos con los reportes generados.

Para realizar el envío se utilizan `smtplib` y `EmailMessage`.

También se deben controlar posibles errores, por ejemplo si no se puede establecer conexión con el servidor SMTP.

## Configuración

Las configuraciones generales del proyecto se encuentran en `config.py`.

De esta manera, si hay que cambiar algún valor utilizado por varios módulos, se puede modificar desde un solo lugar.

Las contraseñas, API keys y otros datos privados no deberían guardarse directamente en el código.

## Instalación

Para ejecutar el proyecto se necesita tener Python instalado.

Las principales librerías utilizadas son:

```text
requests
beautifulsoup4
pandas
```

Se pueden agregar otras librerías en caso de que sean necesarias para los distintos módulos.

## Ejecución

El proyecto debe ejecutarse desde su carpeta principal.

Antes de iniciar el programa hay que verificar que las librerías necesarias estén instaladas y que las configuraciones requeridas estén completas.

## Objetivo final

La idea es que la plataforma pueda juntar toda la información relacionada con los envíos y utilizarla para detectar posibles problemas.

De esta manera se pueden identificar los envíos que necesitan mayor atención, generar un reporte y, cuando corresponda, avisar al cliente.

El proyecto integra varios de los temas vistos durante la cursada, como Python, JSON, APIs, HTTP, scraping, Pandas, ETL y envío de emails.
