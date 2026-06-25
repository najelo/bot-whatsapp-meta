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
            if emoji in ["💖", "⭐", "💎"]:
                ai_utils.set_user_state(phone, f"ESPERANDO_CAPTURE_{emoji}")
                whatsapp_utils.send_whatsapp_message(phone, f"Has elegido {emoji}. Envía el capture para verificar.")
                return {"status": "ok"}

        # 2. Gestión de Texto y PDF
        if 'text' in msg:
            texto = msg['text']['body']
            # Obtenemos todas las posibles, pero controlaremos el envío
            respuestas = ai_utils.buscar_todas_las_respuestas(texto)
            
            # --- CORRECCIÓN: SOLO ENVIAMOS LA PRIMERA PARA EVITAR DUPLICADOS ---
            if respuestas:
                resp = respuestas[0] 
                if resp.startswith("http"):
                    # Enviamos como documento para evitar el error de ".txt"
                    whatsapp_utils.send_whatsapp_document(phone, resp, caption="Aquí tienes tu archivo")
                else:
                    whatsapp_utils.send_whatsapp_message(phone, resp)

        # 3. Gestión de Imágenes
        elif 'image' in msg:
            # ... (tu lógica de imágenes actual se mantiene igual) ...
            pass

    except Exception as e:
        print(f"Error crítico en web_server: {e}")
    return {"status": "ok"}
