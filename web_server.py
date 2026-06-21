import os
import requests
import google.generativeai as genai
from fastapi import FastAPI, Request

app = FastAPI()

# Configurar Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.get("/webhook")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == os.getenv("VERIFY_TOKEN"):
        return int(request.query_params.get("hub.challenge"))
    return "Error"

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    
    try:
        entry = data['entry'][0]['changes'][0]['value']
        if 'messages' in entry:
            message = entry['messages'][0]
            phone_number = message['from']
            text = message['text']['body']
            
            print(f"Recibido de {phone_number}: {text}")
            
            # 1. Preguntar a Gemini
            response = model.generate_content(text)
            respuesta_bot = response.text
            
            # 2. Enviar respuesta por WhatsApp
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
    requests.post(url, headers=headers, json=payload)
