# notificaciones_utils.py
import os
import json  # 👈 AGREGADO: Necesario para convertir el teclado a JSON String
import requests

def enviar_alerta_telegram(monto, telefono, razon="Monto o comprobante sospechoso", image_bytes=None):
    """
    Envía la imagen del capture a Telegram con detalles de la alerta
    y botones interactivos para Aceptar o Rechazar el pago directamente.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("⚠️ Alerta: Variables de entorno de Telegram no configuradas.")
        return False

    mensaje = (
        f"🚨 *¡ALERTA DE PAGO MÓVIL!* 🚨\n\n"
        f"👤 *Teléfono:* `{telefono}`\n"
        f"💰 *Monto:* `Bs. {float(monto):,.2f}`\n"
        f"🔍 *Detalle:* {razon}\n\n"
        f"👇 ¿Deseas aprobar manualmente esta transacción?"
    )

    # Botones interactivos que viajan junto con el mensaje
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "🟢 Aceptar Pago", "callback_data": f"aprobar_{telefono}_{monto}"},
                {"text": "🔴 Rechazar", "callback_data": f"rechazar_{telefono}"}
            ]
        ]
    }

    try:
        if image_bytes:
            # Enviar con la fotografía adjunta usando sendPhoto
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            files = {"photo": ("capture.jpg", image_bytes, "image/jpeg")}
            payload = {
                "chat_id": chat_id,
                "caption": mensaje,
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(inline_keyboard)  # 👈 CORREGIDO: Convertido a string JSON
            }
            response = requests.post(url, data=payload, files=files, timeout=10)
        else:
            # Respaldo en texto plano si no se reciben bytes por algún fallo de red
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": mensaje,
                "parse_mode": "Markdown",
                "reply_markup": inline_keyboard  # En sendMessage mediante json=payload va bien como dict
            }
            response = requests.post(url, json=payload, timeout=5)

        if response.status_code == 200:
            return True
        print(f"❌ Error API Telegram: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Fallo crítico al conectar con Telegram: {e}")
        return False
