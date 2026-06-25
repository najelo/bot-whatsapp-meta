import os
import requests
from auth_utils import get_supabase

def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v25.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {"messaging_product": "whatsapp", "to": to, "text": {"body": text}}
    requests.post(url, headers=headers, json=payload)

def send_whatsapp_document(to, pdf_url, caption="Aquí tienes tu archivo"):
    url = f"https://graph.facebook.com/v25.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {
            "link": pdf_url,
            "caption": caption,
            "filename": "documento.pdf"
        }
    }
    requests.post(url, headers=headers, json=payload)

def send_whatsapp_image(to, image_url, caption=""):
    url = f"https://graph.facebook.com/v25.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {
            "link": image_url,
            "caption": caption
        }
    }
    requests.post(url, headers=headers, json=payload)

def send_whatsapp_audio(to, audio_url):
    url = f"https://graph.facebook.com/v25.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "audio",
        "audio": {
            "link": audio_url
        }
    }
    requests.post(url, headers=headers, json=payload)

def get_image_from_meta(media_id):
    headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}
    url = f"https://graph.facebook.com/v25.0/{media_id}"
    response = requests.get(url, headers=headers)
    meta_data = response.json()
    if 'url' in meta_data:
        image_response = requests.get(meta_data['url'], headers=headers)
        return image_response.content
    raise Exception("No se pudo obtener la imagen de Meta.")
