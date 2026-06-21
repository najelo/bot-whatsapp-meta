import os
import requests
from fastapi import FastAPI, Request

app = FastAPI()

# ... (mantén aquí tu función @app.get("/webhook") de verificación) ...

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    
    # Extraemos el número y el mensaje
    try:
        entry = data['entry'][0]['changes'][0]['value']
        if 'messages' in entry:
            message = entry['messages'][0]
            phone_number = message['from']
            
            # --- AQUÍ ESTÁ LA LÓGICA PARA RESPONDER ---
            send_whatsapp_message(phone_number, "¡Hola! He recibido tu mensaje correctamente.")
            
    except Exception as e:
        print(f"Error: {e}")
        
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

    return {"status": "ok"}
