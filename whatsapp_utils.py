import os
import requests

# Variables de entorno leídas desde Render
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = "v25.0"

def send_whatsapp_message(to, text):
    """Envía un mensaje de texto plano a través de la API de WhatsApp."""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {"messaging_product": "whatsapp", "to": to, "text": {"body": text}}
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"❌ Error enviando mensaje ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Excepción en send_whatsapp_message: {e}")

def send_whatsapp_document(to, pdf_url, caption="Aquí tienes tu archivo"):
    """Envía un documento PDF a través de la API de WhatsApp."""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "document",
            "document": {
                "link": pdf_url,
                "caption": caption,
                "filename": "recetario.pdf"
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"❌ Error enviando documento ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Excepción en send_whatsapp_document: {e}")

# =====================================================================
# LÓGICA DE DESCARGA MULTIMEDIA COMPATIBLE CON TU WEB_SERVER.PY
# =====================================================================

def get_media_url(media_id: str) -> str:
    """Consulta a Meta usando el ID multimedia para obtener su URL de descarga."""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{media_id}"
        headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("url")
        print(f"❌ Error al obtener URL de Meta (Status {response.status_code}): {response.text}")
        return None
    except Exception as e:
        print(f"❌ Excepción en get_media_url: {e}")
        return None

def download_media(media_url: str) -> bytes:
    """Descarga los bytes del archivo desde la URL temporal de Meta."""
    try:
        if not media_url:
            return None
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "User-Agent": "Mozilla/5.0"
        }
        response = requests.get(media_url, headers=headers)
        if response.status_code == 200:
            return response.content
        print(f"❌ Error al descargar archivo de Meta (Status {response.status_code})")
        return None
    except Exception as e:
        print(f"❌ Excepción en download_media: {e}")
        return None

def get_image_from_meta(media_id):
    """
    Descarga completa de bytes multimedia invocada por la línea 53 de tu web_server.py.
    """
    url_temporal = get_media_url(media_id)
    if url_temporal:
        bytes_imagen = download_media(url_temporal)
        if bytes_imagen:
            return bytes_imagen
    raise Exception("No se pudo descargar la imagen de Meta correctamente.")
