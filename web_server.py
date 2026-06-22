from fastapi import FastAPI, Request
import ai_utils, whatsapp_utils

app = FastAPI()

@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    try:
        # Extraer información del mensaje de Meta
        msg = data['entry'][0]['changes'][0]['value']['messages'][0]
        phone = msg['from']
        
        # Flujo de Texto
        if 'text' in msg:
            texto = msg['text']['body']
            # 1. Prioridad: Reglas Automáticas
            regla = ai_utils.buscar_respuesta_automatica(texto)
            resp = regla if regla else ai_utils.process_text(texto)
            
            whatsapp_utils.send_whatsapp_message(phone, resp)
            ai_utils.save_to_db(phone, resp, text=texto)
            
        # Flujo de Imagen
        elif 'image' in msg:
            cfg = ai_utils.obtener_datos_verificacion()
            if not cfg:
                whatsapp_utils.send_whatsapp_message(phone, "Sistema de pagos no configurado.")
            else:
                img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
                resp = ai_utils.verificar_pago_movil(
                    img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado']
                )
                whatsapp_utils.send_whatsapp_message(phone, resp)
                ai_utils.save_to_db(phone, resp, url_path=msg['image']['id'])
                
    except Exception as e:
        print(f"Error crítico en webhook: {e}")
        
    return {"status": "ok"}
