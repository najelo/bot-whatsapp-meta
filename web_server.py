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

        # 1. Gestión de Reacciones
        if 'reaction' in msg:
            emoji = msg['reaction'].get('emoji')
            if emoji in ["💎", "⭐", "🚀"]:
                ai_utils.set_user_state(phone, f"ESPERANDO_CAPTURE_{emoji}")
                whatsapp_utils.send_whatsapp_message(phone, f"Has elegido {emoji}. Envía el capture para verificar.")
                return {"status": "ok"}

        # 2. Gestión de Texto y PDF (Lógica original restaurada)
        if 'text' in msg:
            texto = msg['text']['body']
            respuestas = ai_utils.buscar_todas_las_respuestas(texto)
            for resp in respuestas:
                if resp.startswith("http"):
                    whatsapp_utils.send_whatsapp_document(phone, resp, caption="Aquí tienes tu archivo")
                else:
                    whatsapp_utils.send_whatsapp_message(phone, resp)
                time.sleep(1)

        # 3. Gestión de Imágenes (Auditoría)
        elif 'image' in msg:
            estado = ai_utils.get_user_state(phone)
            if estado.startswith("ESPERANDO_CAPTURE_"):
                emoji_usado = estado.split("_")[2]
                monto = ai_utils.obtener_monto_por_emoji(emoji_usado)
                
                img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
                cfg = ai_utils.obtener_datos_verificacion()
                
                res = ai_utils.verificar_pago_movil(img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado'], monto)
                whatsapp_utils.send_whatsapp_message(phone, res)
                
                ai_utils.save_to_db(phone, res, url_path=msg['image']['id'])
                ai_utils.set_user_state(phone, "IDLE")
            else:
                whatsapp_utils.send_whatsapp_message(phone, "No estoy esperando un pago. Reacciona con un emoji para iniciar.")

    except Exception as e:
        print(f"Error crítico en web_server: {e}")
    return {"status": "ok"}
