from fastapi import FastAPI, Request
import ai_utils
import whatsapp_utils

app = FastAPI()

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    
    try:
        entry = data.get('entry', [])
        if not entry: 
            return {"status": "ok"}
        
        value = entry[0].get('changes', [{}])[0].get('value', {})
        
        if 'messages' in value:
            msg = value['messages'][0]
            phone = msg.get('from')
            
            # Lógica de Texto
            if 'text' in msg:
                texto = msg['text']['body']
                print(f"DEBUG: Buscando respuesta para: {texto}")
                
                resp = ai_utils.buscar_respuesta_automatica(texto)
                
                if resp:
                    print(f"DEBUG: Respuesta encontrada: {resp}")
                    whatsapp_utils.send_whatsapp_message(phone, resp)
                    ai_utils.save_to_db(phone, resp, text=texto)
                else:
                    print("DEBUG: No se encontró respuesta.")
                    whatsapp_utils.send_whatsapp_message(phone, "Lo siento, no tengo esa información. Contacta a un administrador.")
                    ai_utils.save_to_db(phone, "Lo siento, no tengo esa información.", text=texto)
            
            # Lógica de Imagen
            elif 'image' in msg:
                img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
                cfg = ai_utils.obtener_datos_verificacion()
                resp = ai_utils.verificar_pago_movil(img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado'])
                
                whatsapp_utils.send_whatsapp_message(phone, resp)
                ai_utils.save_to_db(phone, resp, url_path=msg['image']['id'])
                
    except Exception as e:
        print(f"Error procesando el mensaje: {e}")
        
    return {"status": "ok"}
