from fastapi import FastAPI, Request, BackgroundTasks
import ai_utils
import whatsapp_utils
import time

app = FastAPI()

def enviar_respuestas_segundo_plano(phone: str, texto: str):
    """
    Procesa la búsqueda y el envío secuencial de mensajes en segundo plano
    para que FastAPI responda de inmediato a Meta y no se dupliquen los mensajes.
    """
    # Usamos tu función original de ai_utils para traer la lista de respuestas
    respuestas = ai_utils.buscar_todas_las_respuestas(texto)
    
    if respuestas:
        for resp in respuestas:
            if resp.startswith("http"):
                whatsapp_utils.send_whatsapp_document(phone, resp, caption="Aquí tienes tu archivo")
            else:
                whatsapp_utils.send_whatsapp_message(phone, resp)
            # Mantiene el orden y la separación de los mensajes de la cadena
            time.sleep(1.5)
    else:
        # Si no está en BD, enviamos a tu IA original
        respuesta_ia = ai_utils.generar_respuesta_ia(texto)
        whatsapp_utils.send_whatsapp_message(phone, respuesta_ia)

@app.post("/webhook")
async def handle_message(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    try:
        value = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {})
        if 'messages' not in value: return {"status": "ok"}
        
        msg = value['messages'][0]
        phone = msg.get('from')

        # 1. GESTIÓN DE REACCIONES (Tu lógica original exacta)
        if 'reaction' in msg:
            emoji = msg['reaction'].get('emoji')
            if emoji in ["💖", "⭐", "💎"]:
                ai_utils.set_user_state(phone, f"ESPERANDO_CAPTURE_{emoji}")
                whatsapp_utils.send_whatsapp_message(phone, f"Has elegido {emoji}. Envía el capture para verificar.")
                return {"status": "ok"}

        # 2. GESTIÓN DE TEXTO Y PDF (Solo se cambió el envío a background_tasks)
        if 'text' in msg:
            texto = msg['text']['body']
            
            # Ejecutamos la lógica en segundo plano y respondemos 200 OK inmediatamente a Meta
            background_tasks.add_task(enviar_respuestas_segundo_plano, phone, texto)
            return {"status": "ok"}

        # 3. GESTIÓN DE IMÁGENES (Tu lógica original exacta de verificación de pagos)
        elif 'image' in msg:
            estado = ai_utils.get_user_state(phone)
            if estado.startswith("ESPERANDO_CAPTURE_"):
                emoji_usado = estado.split("_")[2]
                monto = ai_utils.obtener_monto_por_emoji(emoji_usado)
                
                # Procesar imagen
                img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
                cfg = ai_utils.obtener_datos_verificacion()
                
                # Verificar con IA
                res = ai_utils.verificar_pago_movil(img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado'], monto)
                whatsapp_utils.send_whatsapp_message(phone, res)
                
                # Guardar en BD
                ai_utils.save_to_db(phone, res, url_path=msg['image']['id'])
                ai_utils.set_user_state(phone, "IDLE")
            else:
                whatsapp_utils.send_whatsapp_message(phone, "No estoy esperando un capture tuyo en este momento.")

    except Exception as e:
        print(f"Error en Webhook: {e}")
        
    return {"status": "ok"}
