import requests
import json
from decouple import config

# Obtener variables desde el archivo .env
TOKEN = config("TOKEN")
PHONE_NUMBER_ID = config("PHONE_NUMBER_ID")
VERSION = "v21.0" # Asegúrate de que esta versión sea la que usas

def enviar_mensaje(data):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    contenido = data.get("body")
    numero = data.get("to")

    # --- LÓGICA INTELIGENTE DE ENVÍO ---
    # Si el contenido es un link (archivo PDF de Supabase)
    if contenido.startswith("http"):
        payload = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "document",
            "document": {
                "link": contenido,
                "caption": "Aquí tienes tu archivo",
                "filename": "recetario.pdf"
            }
        }
    else:
        # Si es texto normal
        payload = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "text",
            "text": {"body": contenido}
        }
    # -----------------------------------

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar a WhatsApp: {e}")
        return None
(url, headers=headers)
    meta_data = response.json()
    if 'url' in meta_data:
        image_response = requests.get(meta_data['url'], headers=headers)
        return image_response.content
    raise Exception("No se pudo obtener la imagen de Meta.")
