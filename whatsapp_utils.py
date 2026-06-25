import os
import requests

# Variables de entorno configuradas en Render
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
# Reemplaza con tu ID de teléfono de la API de WhatsApp (el que envía los mensajes)
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID", "tu_phone_number_id_aqui")
VERSION = "v20.0"

# =====================================================================
# FUNCIONES DE ENVÍO (Las que te hacían falta)
# =====================================================================

def send_whatsapp_message(to_phone: str, text: str):
    """Envía un mensaje de texto plano a través de la API de WhatsApp."""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {"preview_url": False, "body": text}
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"❌ Error enviando mensaje de texto ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Excepción enviando mensaje de texto: {e}")

def send_whatsapp_document(to_phone: str, document_url: str, filename: str):
    """Envía un documento PDF o archivo multimedia por URL."""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename
            }
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"❌ Error enviando documento ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Excepción enviando documento: {e}")

def send_whatsapp_image(to_phone: str, image_url: str):
    """Envía una imagen por URL."""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "image",
            "image": {"link": image_url}
        }
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"❌ Excepción enviando imagen: {e}")

def send_whatsapp_audio(to_phone: str, audio_url: str):
    """Envía un archivo de audio por URL."""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "audio",
            "audio": {"link": audio_url}
        }
        response = requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(f"❌ Excepción enviando audio: {e}")


# =====================================================================
# FUNCIONES DE DESCARGA DE MULTIMEDIA
# =====================================================================

def get_media_url(media_id: str) -> str:
    """Consulta a Meta usando el ID del archivo multimedia para obtener su URL temporal."""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{media_id}"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json().get("url")
        else:
            print(f"❌ Error al obtener URL de multimedia de Meta (Status {response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"❌ Excepción al obtener URL de multimedia: {e}")
        return None

def download_media(media_url: str) -> bytes:
    """Descarga en memoria los bytes de la imagen desde los servidores de Meta."""
    try:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(media_url, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            print(f"❌ Error al descargar archivo desde Meta (Status {response.status_code})")
            return None
    except Exception as e:
        print(f"❌ Excepción al descargar archivo de Meta: {e}")
        return None
