from fastapi import FastAPI, Request, HTTPException
import os

app = FastAPI()

@app.get("/webhook")
async def verify_webhook(request: Request):
    # Obtener los parámetros enviados por Meta
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # Verificar que el modo y el token coincidan
    if mode == "subscribe" and token == os.getenv("VERIFY_TOKEN"):
        return int(challenge) # Devuelve el challenge si el token es correcto
    else:
        raise HTTPException(status_code=403, detail="Token de verificación incorrecto")

@app.post("/webhook")
async def handle_webhook(request: Request):
    # Aquí irá la lógica para recibir los mensajes de WhatsApp
    return {"status": "ok"}
