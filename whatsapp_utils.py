import requests
import os

# Asegúrate de tener estas variables de entorno configuradas en tu servidor (Render)
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
VERSION = "v20.0"  # O la versión de Graph API que estés utilizando

def get_media_url(media_id: str) -> str:
    """
    Consulta a la API de Meta usando el ID del archivo multimedia 
    para obtener su URL de descarga temporal.
    """
    try:
        url = f"https://graph.facebook.com/{VERSION}/{media_id}"
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}"
        }
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # Meta nos devuelve un JSON con la clave 'url'
            return response.json().get("url")
        else:
            print(f"❌ Error al obtener URL de multimedia de Meta (Status {response.status_code}): {response.text}")
            return None
    except Exception as e:
        print(f"❌ Excepción al obtener URL de multimedia: {e}")
        return None

def download_media(media_url: str) -> bytes:
    """
    Descarga los bytes del archivo desde la URL temporal provista por Meta.
    """
    try:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "User-Agent": "Mozilla/5.0"  # Meta a veces bloquea peticiones sin User-Agent definido
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
