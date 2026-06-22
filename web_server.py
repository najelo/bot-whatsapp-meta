from fastapi import FastAPI, Request
import ai_utils, whatsapp_utils

app = FastAPI()

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    try:
        value = data['entry'][0]['changes'][0]['value']
        if 'messages' not in value: return {"status": "ok"}
        
        msg = value['messages'][0]
        phone = msg['from']
        
        # LÓGICA DE PAGO
        if 'image' in msg:
            cfg = ai_utils.obtener_datos_verificacion()
            img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
            resp = ai_utils.verificar_pago_movil(img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado'])
            whatsapp_utils.send_whatsapp_message(phone, resp)
            ai_utils.save_to_db(phone, resp, url_path=msg['image']['id'])
            
        # LÓGICA DE CONSULTA (IA + BD)
     elif 'text' in msg:
            texto = msg['text']['body']
            # Primero intentamos FAQ (Respuesta inmediata)
            regla = ai_utils.buscar_respuesta_automatica(texto)
            
            if regla:
                resp = regla
            else:
                # Si no es FAQ, vamos a la IA con el mensaje de "no encontrado" configurado arriba
                resp = ai_utils.responder_pregunta_usuario(texto)
                
            whatsapp_utils.send_whatsapp_message(phone, resp)
            ai_utils.save_to_db(phone, resp, text=texto)
            
    except Exception as e:
        print(f"Error: {e}")
        
    return {"status": "ok"}
