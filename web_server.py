import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

# Tu función de verificación que ya tienes
@app.get("/webhook")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == os.getenv("VERIFY_TOKEN"):
        return int(request.query_params.get("hub.challenge"))
    return "Error"

# Tu función para procesar mensajes
@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    
    try:
        # Extraer información del mensaje
        entry = data['entry'][0]['changes'][0]['value']
        if 'messages' in entry:
            message = entry['messages'][0]
            phone_number = message['from']
            text = message['text']['body']
            
            print(f"Recibido de {phone_number}: {text}")
            
            # --- AQUÍ LLAMAS A LA FUNCIÓN PARA RESPONDER ---
            send_whatsapp_message(phone_number, "¡Hola! He recibido tu mensaje correctamente.")
            
    except Exception as e:
        print(f"Error procesando: {e}")
        
    return {"status": "ok"}

# Función para enviar la respuesta a Meta
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
