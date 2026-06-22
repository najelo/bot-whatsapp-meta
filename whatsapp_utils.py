import os
import requests

def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v25.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {"messaging_product": "whatsapp", "to": to, "text": {"body": text}}
    requests.post(url, headers=headers, json=payload)

def get_image_from_meta(media_id):
    headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}
    url = f"https://graph.facebook.com/v25.0/{media_id}"
    
    response = requests.get(url, headers=headers)
    meta_data = response.json()
    
    # Si Meta devuelve un error, lo imprimimos claramente
    if 'error' in meta_data:
        print(f"DEBUG Meta Error: {meta_data['error']}")
        raise Exception(f"Error de Meta: {meta_data['error']['message']}")
    
    # Verificamos si 'url' existe en la respuesta
    if 'url' in meta_data:
        image_response = requests.get(meta_data['url'], headers=headers)
        return image_response.content
    else:
        # Esto es lo que causaba tu error. Ahora sabremos qué trae el JSON.
        print(f"DEBUG: JSON recibido de Meta: {meta_data}")
        raise Exception("El JSON de Meta no contiene la clave 'url'. Revisa el log de arriba.")
