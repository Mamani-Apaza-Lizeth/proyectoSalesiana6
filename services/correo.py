"""
Servicio de correo independiente (sección 25 de la especificación).

Si las credenciales SMTP no están configuradas, el sistema sigue funcionando
en "modo de desarrollo": el correo se imprime en la consola en lugar de
enviarse, para no bloquear las pruebas.
"""
import smtplib
from email.mime.text import MIMEText
from flask import current_app


def _enviar(destinatario, asunto, cuerpo):
    cfg = current_app.config
    if cfg.get("CORREO_MODO_DESARROLLO"):
        print("=" * 60)
        print("[CORREO - MODO DESARROLLO, no se envió realmente]")
        print(f"Para: {destinatario}")
        print(f"Asunto: {asunto}")
        print(cuerpo)
        print("=" * 60)
        return True

    try:
        msg = MIMEText(cuerpo)
        msg["Subject"] = asunto
        msg["From"] = cfg["MAIL_USERNAME"]
        msg["To"] = destinatario

        with smtplib.SMTP(cfg["MAIL_SERVER"], cfg["MAIL_PORT"]) as server:
            server.starttls()
            server.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
            server.sendmail(cfg["MAIL_USERNAME"], [destinatario], msg.as_string())
        return True
    except Exception as e:
        print(f"[CORREO] Error enviando correo a {destinatario}: {e}")
        return False


def enviar_bienvenida(usuario):
    asunto = "Bienvenido a Cotillón MiraLiz"
    cuerpo = (
        f"Hola {usuario.nombre_completo},\n\n"
        "Tu cuenta ha sido creada exitosamente en Cotillón MiraLiz.\n"
        "Ya puedes iniciar sesión y realizar tus pedidos.\n\n"
        "Saludos,\nEquipo MiraLiz"
    )
    return _enviar(usuario.correo, asunto, cuerpo)


def enviar_alerta_stock_bajo(insumo):
    cfg = current_app.config
    asunto = f"⚠ Stock bajo: {insumo.nombre}"
    cuerpo = (
        f"El insumo '{insumo.nombre}' llegó a un nivel de stock bajo.\n\n"
        f"Disponible: {insumo.stock_actual} {insumo.unidad}\n"
        f"Stock mínimo: {insumo.stock_minimo} {insumo.unidad}\n\n"
        "Por favor revisa el inventario en el panel administrativo."
    )
    return _enviar(cfg["MAIL_DUENO"], asunto, cuerpo)
