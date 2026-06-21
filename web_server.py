from fastapi import FastAPI, Request
import os
import requests

app = FastAPI()

# La parte que ya configuraste para verificar
@app.get("/webhook")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == os.getenv("VERIFY_TOKEN"):
        return int(request.query_params.get("hub.challenge"))
    return "Error"

# LA PARTE NUEVA: Aquí recibes el mensaje real
@app.post("/webhook")
async def handle_message(request: Request):
    body = await request.json()
    
    # Aquí puedes extraer el mensaje
    try:
        entry = body['entry'][0]
        changes = entry['changes'][0]
        message = changes['value']['messages'][0]
        phone_number = message['from']
        text = message['text']['body']
        
        print(f"Mensaje recibido de {phone_number}: {text}")
        
        # AQUÍ ES DONDE LLAMARÍAS A LA API DE META PARA RESPONDER
        # O A GEMINI PARA GENERAR LA RESPUESTA
        
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

    return {"status": "ok"}
