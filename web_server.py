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

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# 2. Funciones Auxiliares
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
    print(f"DEBUG Meta: {response.status_code} - {response.text}")

def get_image_from_meta(media_id):
    headers = {"Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}"}
    url = f"https://graph.facebook.com/v25.0/{media_id}"
    meta_resp = requests.get(url, headers=headers).json()
    return requests.get(meta_resp['url'], headers=headers).content

# 3. Webhook Endpoints
@app.get("/webhook")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == os.getenv("VERIFY_TOKEN"):
        return int(request.query_params.get("hub.challenge"))
    return {"error": "Invalid token"}, 403

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    try:
        value = data['entry'][0]['changes'][0]['value']
        if 'messages' in value:
            msg = value['messages'][0]
            phone = msg['from']

            # CASO TEXTO
            if 'text' in msg:
                user_text = msg['text']['body']
                response = model.generate_content(user_text)
                
                send_whatsapp_message(phone, response.text)
                supabase.table("mensajes").insert({
                    "phone": phone, 
                    "texto": user_text, 
                    "respuesta": response.text
                }).execute()

            # CASO IMAGEN
            elif 'image' in msg:
                media_id = msg['image']['id']
                img_bytes = get_image_from_meta(media_id)
                
                # Subir a Supabase
                path = f"media/{phone}/{media_id}.jpg"
                supabase.storage.from_("whatsapp-media").upload(path, img_bytes, {"content-type": "image/jpeg"})
                
                # Procesar en Gemini
                img = PIL.Image.open(io.BytesIO(img_bytes))
                response = model.generate_content(["Describe esta imagen:", img])
                
                # Responder y Log
                final_resp = response.text
                send_whatsapp_message(phone, final_resp)
                supabase.table("mensajes").insert({
                    "phone": phone, 
                    "url_archivo": path, 
                    "respuesta": final_resp
                }).execute()

    except Exception as e:
        print(f"DEBUG ERROR CRÍTICO: {e}")
    
    return {"status": "ok"}
