from fastapi import FastAPI, Request, Response
import os

app = FastAPI()

# Este endpoint es el ÚNICO que Meta necesita para validar
@app.get("/webhook")
async def verify(request: Request):
    # Obtenemos los parámetros directamente
    query_params = request.query_params
    mode = query_params.get("hub.mode")
    token = query_params.get("hub.verify_token")
    challenge = query_params.get("hub.challenge")

    # Validación estricta
    if mode == "subscribe" and token == os.getenv("VERIFY_TOKEN"):
        # Devolvemos SOLO el texto del challenge, sin nada más
        return Response(content=challenge, media_type="text/plain", status_code=200)
    
    return Response(content="Forbidden", status_code=403)

# Este es el que recibirá los mensajes reales después de validar
@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    print("¡Mensaje recibido de Meta!:", data)
    return {"status": "ok"}