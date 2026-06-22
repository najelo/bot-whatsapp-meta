from fastapi import FastAPI, Request
from whatsapp_utils import send_whatsapp_message, get_image_from_meta
import ai_utils
import os

app = FastAPI()

@app.get("/webhook")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == os.getenv("VERIFY_TOKEN"):
        return int(request.query_params.get("hub.challenge"))
    return {"error": "Invalid token"}, 403

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    try:
        # Extraer el valor del mensaje
        value = data['entry'][0]['changes'][0]['value']
        if 'messages' in value:
            msg = value['messages'][0]
            phone = msg['from']
            
            # Lógica de procesamiento
            if 'text' in msg:
                resp = ai_utils.process_text(msg['text']['body'])
                send_whatsapp_message(phone, resp)
                ai_utils.save_to_db(phone, resp, text=msg['text']['body'])
                
            elif 'image' in msg:
                img_bytes = get_image_from_meta(msg['image']['id'])
                resp = ai_utils.process_image(img_bytes)
                send_whatsapp_message(phone, resp)
                # Aquí guardamos el path, por ejemplo:
                path = f"media/{phone}/{msg['image']['id']}.jpg"
                ai_utils.save_to_db(phone, resp, url_path=path)
                
    except Exception as e:
        print(f"Error procesando mensaje: {e}")
        
    return {"status": "ok"}