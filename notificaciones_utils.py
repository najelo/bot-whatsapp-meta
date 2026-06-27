# notificaciones_utils.py
import os
import json
import requests

def enviar_alerta_telegram(monto, telefono, razon="Monto o comprobante sospechoso", image_bytes=None, tipo_alerta="alerta"):
    """
    Envía alertas a Telegram divididas por canales/chats según el tipo_alerta:
    - 'alerta': Para comprobantes rechazados o sospechosos.
    - 'error': Para fallas críticas del servidor o excepciones de código.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # 🔀 SEPARACIÓN EN DOS PARTES SEGÚN EL TIPO
    if tipo_alerta == "error":
        chat_id = os.getenv("TELEGRAM_CHAT_ID_ERRORES")
        titulo = "⚠️ *FALLA CRÍTICA DEL SISTEMA* ⚠️"
    else:
        chat_id = os.getenv("TELEGRAM_CHAT_ID_RECHAZOS")
        titulo = "🚨 *COMPROBANTE RECHAZADO* 🚨"
    
    if not token or not chat_id:
        print(f"⚠️ Alerta: Variables de Telegram para '{tipo_alerta}' no configuradas.")
        return False

    mensaje = (
        f"{titulo}\n\n"
        f"👤 *Teléfono:* `{telefono}`\n"
        f"💰 *Monto:* `Bs. {float(monto):,.2f}`\n"
        f"🔍 *Detalle:* {razon}\n\n"
        f"👇 ¿Deseas aprobar manualmente esta transacción?"
    )

    # Los botones interactivos solo son útiles para gestionar los comprobantes
    inline_keyboard = {
        "inline_keyboard": [
            [
                {"text": "🟢 Aceptar Pago", "callback_data": f"aprobar_{telefono}_{monto}"},
                {"text": "🔴 Rechazar", "callback_data": f"rechazar_{telefono}"}
            ]
        ]
    }

    try:
        if image_bytes and tipo_alerta == "alerta":
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            files = {"photo": ("capture.jpg", image_bytes, "image/jpeg")}
            payload = {
                "chat_id": chat_id,
                "caption": mensaje,
                "parse_mode": "Markdown",
                "reply_markup": json.dumps(inline_keyboard)
            }
            response = requests.post(url, data=payload, files=files, timeout=10)
        else:
            # Los errores críticos internos van como texto plano sin botones al chat de fallas
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": mensaje,
                "parse_mode": "Markdown"
            }
            if tipo_alerta == "alerta":
                payload["reply_markup"] = inline_keyboard
                
            response = requests.post(url, json=payload, timeout=5)

        if response.status_code == 200:
            return True
        print(f"❌ Error API Telegram ({tipo_alerta}): {response.text}")
        return False
    except Exception as e:
        print(f"❌ Fallo crítico al conectar con Telegram: {e}")
        return False
