import os
import requests
from auth_utils import get_supabase

# Usamos consistentemente ACCESS_TOKEN que es el que lee tu código original
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = "v25.0" # Tu versión actual configurada

def send_whatsapp_message(to, text):
    """Envía un mensaje de texto plano a través de la API de WhatsApp."""
    try:
        url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp", 
            "to": to, 
            "text": {"body": text}
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code != 200:
            print(f"❌ Error enviando mensaje de texto ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"❌ Excepción enviando mensaje de texto: {e}")

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
        print(f"❌ Excepción enviando documento: {e}")

def get_image_from_meta(media_id):
    """Obtiene y descarga los bytes de la imagen desde los servidores de Meta."""
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    url = f"https://graph.facebook.com/{VERSION}/{media_id}"
    
    response = requests.get(url, headers=headers)
    meta_data = response.json()
    
    if 'url' in meta_data:
        # Añadimos un User-Agent genérico para prevenir bloqueos de descarga
        download_headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "User-Agent": "Mozilla/5.0"
        }
        image_response = requests.get(meta_data['url'], headers=download_headers)
        if image_response.status_code == 200:
            return image_response.content
        else:
            raise Exception(f"Error al descargar los bytes de la imagen. Status: {image_response.status_code}")
            
    raise Exception(f"No se pudo obtener la URL de descarga de Meta. Respuesta: {meta_data}")
