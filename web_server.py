from fastapi import FastAPI, Request
import ai_utils
import whatsapp_utils
import time

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
            
            if 'text' in msg:
                texto = msg['text']['body']
                # Usamos la nueva lógica que devuelve una lista de respuestas
                lista_respuestas = ai_utils.buscar_todas_las_respuestas(texto)
                
                if lista_respuestas:
                    for resp in lista_respuestas:
                        try:
                            # Si es un link de recetarios, lo enviamos como documento
                            if resp.startswith("http") and "recetarios-helado" in resp:
                                whatsapp_utils.send_whatsapp_document(phone, resp, caption="Aquí tienes tu recetario")
                            else:
                                whatsapp_utils.send_whatsapp_message(phone, resp)
                            
                            time.sleep(1.5) # Delay necesario para evitar bloqueos por envío masivo
                            ai_utils.save_to_db(phone, resp, text=texto)
                        except Exception as e:
                            print(f"Error al enviar: {e}")
                else:
                    whatsapp_utils.send_whatsapp_message(phone, "Lo siento, no encontré esa información.")
            
            elif 'image' in msg:
                img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
                cfg = ai_utils.obtener_datos_verificacion()
                resp = ai_utils.verificar_pago_movil(img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado'])
                whatsapp_utils.send_whatsapp_message(phone, resp)
                ai_utils.save_to_db(phone, resp, url_path=msg['image']['id'])
                
    except Exception as e:
        print(f"Error general en webhook: {e}")
    return {"status": "ok"}
