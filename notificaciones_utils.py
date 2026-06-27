# notificaciones_utils.py
import os
import requests

def enviar_alerta_telegram(monto, telefono, razon="Monto incorrecto"):
    """
    Envía una notificación instantánea al Telegram del administrador
    cuando el bot detecta una alerta o posible fraude en el pago.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("⚠️ Error: Las variables de Telegram no están configuradas en el entorno.")
        return

    mensaje = (
        f"🚨 *¡ALERTA DE PAGO MÓVIL!* 🚨\n\n"
        f"👤 *Teléfono Emisor:* {telefono}\n"
        f"💰 *Monto Registrado:* Bs. {monto:.2f}\n"
        f"🔍 *Detalle:* {razon}\n\n"
        f"⚠️ _Por favor, revisa el Panel de Control para verificar manualmente._"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            print(f"❌ Error al enviar a Telegram: {response.text}")
    except Exception as e:
        print(f"❌ Fallo de conexión con la API de Telegram: {e}")
