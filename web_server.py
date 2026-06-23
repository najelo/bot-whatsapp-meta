from fastapi import FastAPI, Request
import ai_utils
import whatsapp_utils
import time

app = FastAPI()

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    try:
        value = data['entry'][0]['changes'][0]['value']
        if 'messages' in value:
            msg = value['messages'][0]
            phone = msg.get('from')
            
            # 1. DETECCIÓN DE REACCIONES
    # 1. DETECCIÓN DE REACCIONES (Mejorada y robusta)
            if 'reaction' in msg:
                # Usamos .get() para evitar el KeyError
                reaction_data = msg.get('reaction', {})
                emoji = reaction_data.get('emoji')
                
                # Verificamos que realmente exista un emoji antes de procesar
                if emoji:
                    if emoji in ["💎", "💖"]:
                        ai_utils.set_user_state(phone, "ESPERANDO_CAPTURE")
                        whatsapp_utils.send_whatsapp_message(phone, "¡Gracias por el apoyo! Envía ahora el capture del pago para verificarlo.")
                        return {"status": "ok"}

            # 2. PROCESAMIENTO DE MENSAJES (Texto o Imagen)
            if 'text' in msg:
                texto = msg['text']['body']
                lista_respuestas = ai_utils.buscar_todas_las_respuestas(texto)
                for resp in lista_respuestas:
                    if resp.startswith("http") and "recetarios-helado" in resp:
                        whatsapp_utils.send_whatsapp_document(phone, resp, caption="Aquí tienes tu recetario")
                    else:
                        whatsapp_utils.send_whatsapp_message(phone, resp)
                    time.sleep(1)
            
            elif 'image' in msg:
                estado = ai_utils.get_user_state(phone)
                if estado == "ESPERANDO_CAPTURE":
                    # Solo audita si el usuario reaccionó previamente
                    img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
                    cfg = ai_utils.obtener_datos_verificacion()
                    resp = ai_utils.verificar_pago_movil(img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado'])
                    whatsapp_utils.send_whatsapp_message(phone, resp)
                    
                    # Limpiamos el estado después de auditar
                    ai_utils.set_user_state(phone, "IDLE")
                    ai_utils.save_to_db(phone, resp, url_path=msg['image']['id'])
                else:
                    whatsapp_utils.send_whatsapp_message(phone, "No estoy esperando un pago ahora mismo. Usa una palabra clave o reacciona para iniciar.")
                
    except Exception as e:
        print(f"Error: {e}")
    return {"status": "ok"}
