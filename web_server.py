import os
import requests
import google.generativeai as genai
from fastapi import FastAPI, Request

app = FastAPI()

# 1. Configurar Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Cambia tu línea actual por esta:
model = genai.GenerativeModel('models/gemini-1.5-flash')

# 2. Tu Webhook para Meta
@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    
    try:
        # Extraer mensaje del JSON de Meta
        message_data = data['entry'][0]['changes'][0]['value']['messages'][0]
        phone_number = message_data['from']
        text = message_data['text']['body']
        
        # 3. Generar respuesta con Gemini
        response = model.generate_content(text)
        respuesta_bot = response.text
        
        # 4. Enviar respuesta por WhatsApp
        enviar_respuesta_whatsapp(phone_number, respuesta_bot)
        
    except Exception as e:
        print(f"Error procesando: {e}")
        
    return {"status": "ok"}

# Modifica tu función de envío así para ver qué responde Meta:
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
    # ESTO ES LO QUE NECESITAMOS VER EN LOS LOGS:
    print(f"DEBUG: Meta respondió con código {response.status_code}")
    print(f"DEBUG: Cuerpo de respuesta de Meta: {response.text}")
