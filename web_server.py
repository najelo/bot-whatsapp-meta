from fastapi import FastAPI, Request
import ai_utils
import whatsapp_utils

app = FastAPI()

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    
    try:
        # Validación básica de estructura de Meta
        entry = data.get('entry', [])
        if not entry: 
            return {"status": "ok"}
        
        changes = entry[0].get('changes', [{}])
        if not changes:
            return {"status": "ok"}
            
        value = changes[0].get('value', {})
        
        # Filtramos para asegurarnos de que hay mensajes reales
        if 'messages' in value:
            msg = value['messages'][0]
            phone = msg.get('from')
            
            # --- FILTRO DE SEGURIDAD CRÍTICO ---
            # Si el mensaje no es texto NI imagen, ignoramos (evita respuestas a estados)
            if 'text' not in msg and 'image' not in msg:
                return {"status": "ok"}
            
            # Lógica para Texto
            if 'text' in msg:
                texto = msg['text']['body']
                print(f"DEBUG: Procesando mensaje de {phone}: {texto}")
                
                resp = ai_utils.buscar_respuesta_automatica(texto)
                
                if resp:
                    try:
                        whatsapp_utils.send_whatsapp_message(phone, resp)
                        ai_utils.save_to_db(phone, resp, text=texto)
                    except Exception as e:
                        print(f"DEBUG: ¡ERROR al enviar mensaje de WhatsApp!: {e}")
                else:
                    # Respuesta por defecto si no hay regla
                    msg_default = "Lo siento, no tengo esa información. Contacta a un administrador."
                    whatsapp_utils.send_whatsapp_message(phone, msg_default)
                    ai_utils.save_to_db(phone, msg_default, text=texto)
            
            # Lógica para Imagen
            elif 'image' in msg:
                print(f"DEBUG: Procesando imagen de {phone}")
                img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
                cfg = ai_utils.obtener_datos_verificacion()
                
                # Verificamos pago
                resp = ai_utils.verificar_pago_movil(img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado'])
                
                whatsapp_utils.send_whatsapp_message(phone, resp)
                ai_utils.save_to_db(phone, resp, url_path=msg['image']['id'])
                
    except Exception as e:
        print(f"Error general en webhook: {e}")
        
    return {"status": "ok"}
