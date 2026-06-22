import os
import requests
import time
from auth_utils import get_supabase

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
    
    if 'url' in meta_data:
        image_response = requests.get(meta_data['url'], headers=headers)
        return image_response.content
    else:
        raise Exception("El JSON de Meta no contiene la clave 'url'.")

def obtener_datos_pago_activos():
    """Consulta Supabase con hasta 3 reintentos para evitar errores de conexión."""
    for i in range(3):
        try:
            supabase = get_supabase()
            response = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Intento {i+1} fallido, esperando 5s... Error: {e}")
            time.sleep(5)  # Espera antes de reintentar
    return None
