import os
import requests
from auth_utils import get_supabase

# --- Funciones de Meta (ya existentes) ---
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

# --- Nueva lógica para Supabase (Integración de Pagos) ---
def obtener_datos_pago_activos():
    """Consulta Supabase para obtener el registro que tenga 'activo' como TRUE."""
    try:
        supabase = get_supabase()
        # Buscamos en la tabla configuracion_pago donde activo = True
        response = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
        datos = response.data
        
        if datos:
            return datos[0] # Retorna el primer registro activo encontrado
        return None
    except Exception as e:
        print(f"Error consultando Supabase: {e}")
        return None
