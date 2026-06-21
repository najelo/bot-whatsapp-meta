import os
import requests
import google.generativeai as genai
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv() # Asegúrate de cargar tus variables de entorno
app = FastAPI()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash') # Verifica que la versión sea válida

# --- 1. Verificación del Webhook (Necesario para Meta) ---
@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    
    if mode == "subscribe" and token == os.getenv("VERIFY_TOKEN"):
        return int(challenge)
    return {"error": "Invalid token"}, 403

# --- 2. Recepción de mensajes ---
@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    
    try:
        # Validación de que el mensaje existe
        entry = data.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        
        if 'messages' in value:
            message_data = value['messages'][0]
            phone_number = message_data['from']
            text = message_data['text']['body']
            
            # Generar respuesta con Gemini
            response = model.generate_content(text)
            respuesta_bot = response.text
            
            # Llamar a la función correctamente escrita
            send_whatsapp_message(phone_number, respuesta_bot)
        
    except Exception as e:
        print(f"Error procesando: {e}")
        
    return {"status": "ok"}

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
    print(f"DEBUG: Meta respondió {response.status_code}: {response.text}")
