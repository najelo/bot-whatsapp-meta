from fastapi import FastAPI, Request
import ai_utils, whatsapp_utils

app = FastAPI()

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    print(f"DATOS RECIBIDOS: {data}") # <-- AÑADE ESTO
    # ... resto del código ...
    try:
        value = data['entry'][0]['changes'][0]['value']
        if 'messages' not in value: return {"status": "ok"}
        
        msg = value['messages'][0]
        phone = msg['from']
        
        # Lógica de Imagen (Verificación)
        if 'image' in msg:
            cfg = ai_utils.obtener_datos_verificacion()
            img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
            resp = ai_utils.verificar_pago_movil(img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado'])
            whatsapp_utils.send_whatsapp_message(phone, resp)
            ai_utils.save_to_db(phone, resp, url_path=msg['image']['id'])
            
        # Lógica de Texto (FAQ o IA)
        elif 'text' in msg:
            texto = msg['text']['body']
            regla = ai_utils.buscar_respuesta_automatica(texto)
            if regla:
                resp = regla
            else:
                resp = ai_utils.responder_pregunta_usuario(texto)
                
            whatsapp_utils.send_whatsapp_message(phone, resp)
            ai_utils.save_to_db(phone, resp, text=texto)
            
    except Exception as e:
        print(f"Error: {e}")
    return {"status": "ok"}
