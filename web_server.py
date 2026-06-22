from fastapi import FastAPI, Request
from whatsapp_utils import send_whatsapp_message, get_image_from_meta
import ai_utils

app = FastAPI()

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    try:
        value = data['entry'][0]['changes'][0]['value']
        if 'messages' in value:
            msg = value['messages'][0]
            phone = msg['from']
            
            # --- LÓGICA PARA TEXTO ---
            if 'text' in msg:
                resp = ai_utils.process_text(msg['text']['body'])
                send_whatsapp_message(phone, resp)
                ai_utils.save_to_db(phone, resp, text=msg['text']['body'])
                
            # --- LÓGICA PARA IMAGEN (VERIFICACIÓN DE PAGO) ---
            elif 'image' in msg:
                # 1. Obtener datos de pago configurados en tu BD
                config = ai_utils.obtener_datos_verificacion()
                
                if not config:
                    send_whatsapp_message(phone, "No hay una configuración de pago activa actualmente.")
                    return {"status": "ok"}
                
                # 2. Descargar imagen y verificar
                img_bytes = get_image_from_meta(msg['image']['id'])
                resp = ai_utils.verificar_pago_movil(
                    img_bytes, 
                    config['cedula_esperada'], 
                    config['telefono_esperado']
                )
                
                # 3. Responder al usuario
                send_whatsapp_message(phone, resp)
                
                # 4. Guardar resultado
                path = f"media/{phone}/{msg['image']['id']}.jpg"
                ai_utils.save_to_db(phone, resp, url_path=path)
                
    except Exception as e:
        print(f"Error en el webhook: {e}")
        
    return {"status": "ok"}
