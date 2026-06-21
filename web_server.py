import os
import io
import requests
import PIL.Image
import google.generativeai as genai
from fastapi import FastAPI, Request
from dotenv import load_dotenv
from supabase import create_client

# 1. Configuración
load_dotenv()
app = FastAPI()

# Asegúrate de que el modelo sea el que tienes contratado/accedido
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))

# 2. Funciones de Meta
def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v25.0/{os.environ.get('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.environ.get('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=payload)

def get_image_from_meta(media_id):
    headers = {"Authorization": f"Bearer {os.environ.get('ACCESS_TOKEN')}"}
    url = f"https://graph.facebook.com/v25.0/{media_id}"
    response = requests.get(url, headers=headers)
    meta_data = response.json()
    
    # Depuración de la respuesta de Meta
    print(f"DEBUG Meta data: {meta_data}")
    
    if 'url' in meta_data:
        image_response = requests.get(meta_data['url'], headers=headers)
        return image_response.content
    else:
        raise Exception(f"No se pudo obtener la URL de la imagen. Meta respondió: {meta_data}")

# 3. Webhook
@app.get("/webhook")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == os.environ.get("VERIFY_TOKEN"):
        return int(request.query_params.get("hub.challenge"))
    return {"error": "Invalid token"}, 403

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    # Log para ver qué llega exactamente de Meta
    print(f"DEBUG: Datos recibidos: {data}") 
    
    try:
        value = data['entry'][0]['changes'][0]['value']
        if 'messages' in value:
            msg = value['messages'][0]
            phone = msg['from']
            print(f"DEBUG: Mensaje recibido de {phone}")

            # CASO TEXTO
            if 'text' in msg:
                user_text = msg['text']['body']
                print(f"DEBUG: Procesando texto: {user_text}")
                
                response = model.generate_content(user_text)
                txt_resp = response.text
                
                send_whatsapp_message(phone, txt_resp)
                supabase.table("mensajes").insert({"phone": phone, "texto": user_text, "respuesta": txt_resp}).execute()
            # Procesamiento de IMAGEN
            elif 'image' in msg:
                media_id = msg['image']['id']
                img_bytes = get_image_from_meta(media_id)
                
                # Subir a Supabase
                path = f"media/{phone}/{media_id}.jpg"
                supabase.storage.from_("whatsapp-media").upload(path, img_bytes, {"content-type": "image/jpeg"})
                
                # Procesar en Gemini
                img = PIL.Image.open(io.BytesIO(img_bytes))
                response = model.generate_content(["Describe esta imagen:", img])
                
                send_whatsapp_message(phone, response.text)
                supabase.table("mensajes").insert({"phone": phone, "url_archivo": path, "respuesta": response.text}).execute()

    except Exception as e:
        print(f"DEBUG ERROR CRÍTICO: {e}")
    
    return {"status": "ok"}
