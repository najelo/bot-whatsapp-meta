import os
import io
import requests
import PIL.Image
import google.generativeai as genai
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables desde tu archivo .env
load_dotenv()

app = FastAPI()

# Inicialización de clientes
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Usamos 1.5-flash por ser el más rápido y capaz de ver imágenes
model = genai.GenerativeModel('gemini-1.5-flash') 
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# --- FUNCIONES AUXILIARES ---

def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v25.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"DEBUG: Respuesta de Meta: {response.status_code} - {response.text}")

def get_image_from_meta(media_id):
    headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}
    # 1. Obtener URL de descarga
    url = f"https://graph.facebook.com/v25.0/{media_id}"
    meta_resp = requests.get(url, headers=headers).json()
    # 2. Descargar contenido
    return requests.get(meta_resp['url'], headers=headers).content

# --- ENDPOINTS ---

@app.get("/webhook")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == os.getenv("VERIFY_TOKEN"):
        return int(request.query_params.get("hub.challenge"))
    return {"error": "Invalid token"}, 403

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    try:
        # Navegar por el JSON de Meta
        value = data['entry'][0]['changes'][0]['value']
        if 'messages' in value:
            msg = value['messages'][0]
            phone = msg['from']

            # CASO TEXTO
            if 'text' in msg:
                user_text = msg['text']['body']
                print(f"DEBUG: Procesando texto de {phone}: {user_text}")
                response = model.generate_content(user_text)
                
                send_whatsapp_message(phone, response.text)
                supabase.table("mensajes").insert({"phone": phone, "texto": user_text, "respuesta": response.text}).execute()

            # CASO IMAGEN
            elif 'image' in msg:
                print(f"DEBUG: Procesando imagen de {phone}")
                media_id = msg['image']['id']
                img_bytes = get_image_from_meta(media_id)
                
                # Guardar en Supabase
                path = f"media/{phone}/{media_id}.jpg"
                supabase.storage.from_("whatsapp-media").upload(path, img_bytes, {"content-type": "image/jpeg"})
                public_url = supabase.storage.from_("whatsapp-media").get_public_url(path)
                
                # Analizar con Gemini
                img = PIL.Image.open(io.BytesIO(img_bytes))
                response = model.generate_content(["Describe esta imagen:", img])
                
                send_whatsapp_message(phone, response.text)
                supabase.table("mensajes").insert({"phone": phone, "url_archivo": public_url, "respuesta": response.text}).execute()

    except Exception as e:
        print(f"DEBUG ERROR: {e}")
    
    return {"status": "ok"}
