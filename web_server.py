from fastapi import FastAPI, Request
import ai_utils
import whatsapp_utils

app = FastAPI()

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    try:
        entry = data.get('entry', [])
        if not entry: return {"status": "ok"}
        
        value = entry[0].get('changes', [{}])[0].get('value', {})
        
        if 'messages' in value:
            msg = value['messages'][0]
            phone = msg.get('from')
            
            if 'text' not in msg and 'image' not in msg:
                return {"status": "ok"}
            
            # --- Lógica de Texto y PDF ---
            if 'text' in msg:
                texto = msg['text']['body']
                resp = ai_utils.buscar_respuesta_automatica(texto)
                
                if resp:
                    try:
                        # Si es un enlace de tu bucket, enviamos documento
                        if resp.startswith("http") and "recetarios-helado" in resp:
                            whatsapp_utils.send_whatsapp_document(phone, resp, caption="Aquí tienes tu recetario")
                        else:
                            # Si es texto normal, enviamos mensaje
                            whatsapp_utils.send_whatsapp_message(phone, resp)
                        
                        ai_utils.save_to_db(phone, resp, text=texto)
                    except Exception as e:
                        print(f"Error al enviar: {e}")
                else:
                    whatsapp_utils.send_whatsapp_message(phone, "Lo siento, no encontré esa información.")
            
            # --- Lógica de Imagen ---
            elif 'image' in msg:
                img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
                cfg = ai_utils.obtener_datos_verificacion()
                resp = ai_utils.verificar_pago_movil(img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado'])
                whatsapp_utils.send_whatsapp_message(phone, resp)
                ai_utils.save_to_db(phone, resp, url_path=msg['image']['id'])
                
    except Exception as e:
        print(f"Error general en webhook: {e}")
    return {"status": "ok"}
