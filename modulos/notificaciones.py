import sys
sys.path.append(".")

import os
import smtplib
from email.message import EmailMessage
import pandas as pd
from config import (SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD, DESTINATARIOS_REPORTE, MODO_PRUEBA,
                    TIMEOUT_SEGUNDOS, CARPETA_SALIDAS, PREFIJO_LOG, ENCODING_CSV, ESTADO_CRITICO,
                    ADJUNTOS_REPORTE, TIPOS_ADJUNTO)
from modulos.envios import filtrar_por_estado, armar_asunto_email, generar_mensaje_cliente

# N24
def armar_mensaje(asunto, cuerpo, destinatarios):
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = EMAIL_USER
    msg["To"] = ", ".join(destinatarios)
    msg.set_content(cuerpo)
    return msg

# N24
def agregar_adjunto(msg, ruta, clave):
    tipo, subtipo = TIPOS_ADJUNTO[clave]
    try:
        with open(ruta, "rb") as archivo:
            contenido = archivo.read()
    except FileNotFoundError:
        print("No se encontró el adjunto:", ruta)
        return False
    msg.add_attachment(contenido, maintype=tipo, subtype=subtipo, filename=os.path.basename(ruta))
    return True

def armar_cuerpo_reporte(criticos, fecha):
    lineas = [f"Reporte diario de envíos críticos ({fecha})", ""]
    if len(criticos) == 0:
        lineas.append("Hoy no hay envíos críticos.")
    else:
        lineas.append(f"Cantidad de envíos críticos: {len(criticos)}")
        lineas.append("")
        for envio in criticos:
            lineas.append(f"- {envio['id']} | {envio['cliente']} | zona {envio['zona']} | "
                          f"causa: {envio['causa']} | acción: {envio['accion_recomendada']}")
    lineas.append("")
    lineas.append("Se adjuntan el reporte completo y el gráfico por zona.")
    return "\n".join(lineas)

# N24 y N05
def armar_mensaje_reporte(lista_envios, rutas, fecha):
    criticos = filtrar_por_estado(lista_envios, ESTADO_CRITICO)
    asunto = f"Reporte diario de envíos críticos - {fecha}"
    msg = armar_mensaje(asunto, armar_cuerpo_reporte(criticos, fecha), DESTINATARIOS_REPORTE)
    for clave in ADJUNTOS_REPORTE:
        if clave in rutas:
            agregar_adjunto(msg, rutas[clave], clave)
    return msg

def armar_resultado(destinatarios, asunto, adjuntos, resultado, detalle=""):
    return {
        "fecha_hora": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "destinatarios": destinatarios,
        "asunto": asunto,
        "adjuntos": adjuntos,
        "resultado": resultado,
        "detalle": detalle,
    }

# N24
def armar_mensajes_clientes(lista_envios):
    mensajes = []
    omitidos = []
    for envio in lista_envios:
        if envio["estado"] == "En término":
            continue
        asunto = armar_asunto_email(envio)
        if not envio["email_valido"]:
            omitidos.append(armar_resultado(envio["email"], asunto, "", "Omitido", "Email inválido"))
            continue
        cuerpo = generar_mensaje_cliente(envio)
        destinatarios = [envio["email"]]
        if MODO_PRUEBA:
            # en las pruebas no se le escribe a los clientes de la muestra: va todo al equipo
            asunto = f"[PRUEBA para {envio['email']}] {asunto}"
            destinatarios = DESTINATARIOS_REPORTE
        mensajes.append(armar_mensaje(asunto, cuerpo, destinatarios))
    return mensajes, omitidos

def resultado_de_mensaje(msg, resultado, detalle=""):
    nombres = []
    for parte in msg.iter_attachments():
        nombres.append(parte.get_filename())
    return armar_resultado(msg["To"], msg["Subject"], ", ".join(nombres), resultado, detalle)

# N24
def enviar_mensajes(mensajes):
    resultados = []
    fallo_general = None
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=TIMEOUT_SEGUNDOS) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            try:
                server.login(EMAIL_USER, EMAIL_PASSWORD)
            except smtplib.SMTPAuthenticationError as error:
                fallo_general = f"Autenticación rechazada: {error}"
            if fallo_general is None:
                for msg in mensajes:
                    try:
                        server.send_message(msg)
                        resultados.append(resultado_de_mensaje(msg, "Enviado"))
                    except smtplib.SMTPException as error:
                        resultados.append(resultado_de_mensaje(msg, "Error", f"SMTP: {error}"))
    except (smtplib.SMTPException, OSError) as error:
        # OSError cubre cuando no hay conexión o el servidor no responde
        fallo_general = f"No se pudo usar el servidor SMTP: {error}"

    # lo que no se alcanzó a procesar también queda registrado como error
    for msg in mensajes[len(resultados):]:
        resultados.append(resultado_de_mensaje(msg, "Error", fallo_general))
    return resultados

def guardar_log(resultados, carpeta, fecha):
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"{PREFIJO_LOG}{fecha}.csv")
    df_log = pd.DataFrame(resultados)
    if os.path.exists(ruta):
        df_log.to_csv(ruta, mode="a", header=False, index=False, encoding="utf-8")
    else:
        df_log.to_csv(ruta, index=False, encoding=ENCODING_CSV)
    return ruta

# N24
def enviar_notificaciones(lista_envios, rutas, carpeta=CARPETA_SALIDAS, fecha=None):
    if fecha is None:
        fecha = pd.Timestamp.today().strftime("%Y-%m-%d")
    if EMAIL_USER == "" or EMAIL_PASSWORD == "" or len(DESTINATARIOS_REPORTE) == 0:
        print("Correo sin configurar (faltan EMAIL_USER, EMAIL_PASSWORD o DESTINATARIOS_REPORTE en claves.py), "
              "no se envían emails")
        return []
    if MODO_PRUEBA:
        print("Modo prueba: los avisos a clientes se mandan a los destinatarios del reporte")

    mensajes = [armar_mensaje_reporte(lista_envios, rutas, fecha)]
    mensajes_clientes, omitidos = armar_mensajes_clientes(lista_envios)
    mensajes += mensajes_clientes
    resultados = omitidos + enviar_mensajes(mensajes)
    ruta_log = guardar_log(resultados, carpeta, fecha)

    enviados = 0
    con_error = 0
    for resultado in resultados:
        if resultado["resultado"] == "Enviado":
            enviados += 1
        elif resultado["resultado"] == "Error":
            con_error += 1
            print(f"Error al enviar '{resultado['asunto']}': {resultado['detalle']}")
    print(f"Emails enviados: {enviados} | con error: {con_error} | omitidos: {len(omitidos)}")
    print("Registro de correos:", ruta_log)
    return resultados

if __name__ == "__main__":
    if EMAIL_USER == "" or len(DESTINATARIOS_REPORTE) == 0:
        print("Falta configurar EMAIL_USER, EMAIL_PASSWORD y DESTINATARIOS_REPORTE en claves.py")
    else:
        prueba = armar_mensaje("Prueba de correo", "Este es un correo de prueba enviado desde Python.",
                               DESTINATARIOS_REPORTE)
        for resultado in enviar_mensajes([prueba]):
            print(resultado)