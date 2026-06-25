from fastapi import FastAPI, Request
import ai_utils
import whatsapp_utils
import time

app = FastAPI()

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    try:
        value = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {})
        if 'messages' not in value: return {"status": "ok"}
        
        msg = value['messages'][0]
        phone = msg.get('from')

        # 1. GESTIÓN DE REACCIONES (Verificación de Pago)
        if 'reaction' in msg:
            emoji = msg['reaction'].get('emoji')
            if emoji in ["💖", "⭐", "💎"]:
                ai_utils.set_user_state(phone, f"ESPERANDO_CAPTURE_{emoji}")
                whatsapp_utils.send_whatsapp_message(phone, f"Has elegido {emoji}. Envía el capture para verificar.")
                return {"status": "ok"}

        # 2. GESTIÓN DE TEXTO / RESPUESTAS EN CADENA MULTIMEDIA
        if 'text' in msg:
            texto = msg['text']['body']
            
            # Obtenemos todos los pasos/mensajes asignados a la palabra clave
            respuestas_cadena = ai_utils.buscar_respuestas_en_cadena(texto)
            
            if respuestas_cadena:
                for resp in respuestas_cadena:
                    tipo = resp["tipo"]
                    contenido = resp["contenido"]
                    
                    # Ejecutamos el envío correcto basándonos en el tipo de contenido
                    if tipo == "documento":
                        whatsapp_utils.send_whatsapp_document(phone, contenido, caption="Aquí tienes el documento solicitado.")
                    elif tipo == "multimedia":
                        whatsapp_utils.send_whatsapp_image(phone, contenido, caption="")
                    elif tipo == "audio":
                        whatsapp_utils.send_whatsapp_audio(phone, contenido)
                    else:
                        # Tipo texto simple por defecto
                        whatsapp_utils.send_whatsapp_message(phone, contenido)
                        
                    # Agregamos una pausa de 1 segundo entre envíos para simular comportamiento humano
                    time.sleep(1)
            else:
                # Si no existe ninguna regla activa en BD, responde la IA de Gemini
                respuesta_ia = ai_utils.generar_respuesta_ia(texto)
                whatsapp_utils.send_whatsapp_message(phone, respuesta_ia)

        # 3. GESTIÓN DE IMÁGENES
        elif 'image' in msg:
            estado = ai_utils.get_user_state(phone)
            if estado.startswith("ESPERANDO_CAPTURE_"):
                emoji_usado = estado.split("_")[2]
                monto = ai_utils.obtener_monto_por_emoji(emoji_usado)
                
                # Procesar imagen recibida
                img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
                cfg = ai_utils.obtener_datos_verificacion()
                
                # Verificar capture mediante la IA
                res = ai_utils.verificar_pago_movil(img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado'], monto)
                whatsapp_utils.send_whatsapp_message(phone, res)
                
                # Guardar registro en base de datos e histórico
                ai_utils.save_to_db(phone, res, url_path=msg['image']['id'])
                ai_utils.set_user_state(phone, "IDLE")
            else:
                whatsapp_utils.send_whatsapp_message(phone, "No estoy esperando un pago. Reacciona con un emoji (💖, ⭐ o 💎) a cualquier mensaje para iniciar.")

    except Exception as e:
        print(f"Error crítico en web_server: {e}")
        
    return {"status": "ok"}
