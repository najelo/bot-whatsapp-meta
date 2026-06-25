from fastapi import FastAPI, Request, BackgroundTasks
import ai_utils
import whatsapp_utils
import time
from auth_utils import get_supabase

app = FastAPI()

def enviar_cadena_mensajes(phone: str, reglas_encontradas: list):
    """
    Procesa de manera segura el envío de la secuencia de mensajes en segundo plano
    sin interrumpir la comunicación con el servidor ni con Meta.
    """
    supabase = get_supabase()
    for regla in reglas_encontradas:
        try:
            resp_data = supabase.table("respuestas").select("contenido, tipo_contenido").eq("id", regla['respuesta_id']).execute().data
            if resp_data:
                info_resp = resp_data[0]
                tipo = info_resp['tipo_contenido']
                contenido = info_resp['contenido']
                
                # Enviar utilizando las funciones nativas de tu whatsapp_utils
                if tipo == "texto":
                    whatsapp_utils.send_whatsapp_message(phone, contenido)
                elif tipo == "documento":
                    whatsapp_utils.send_whatsapp_document(phone, contenido)
                elif tipo == "multimedia":
                    whatsapp_utils.send_whatsapp_image(phone, contenido)
                elif tipo == "audio":
                    whatsapp_utils.send_whatsapp_audio(phone, contenido)
                
                # Pausa controlada para simular el orden natural de escritura
                time.sleep(1.5)
        except Exception as e:
            print(f"Error enviando paso de la secuencia: {e}")

@app.post("/webhook")
async def handle_message(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    try:
        value = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {})
        if 'messages' not in value: 
            return {"status": "ok"}
        
        msg = value['messages'][0]
        phone = msg.get('from')

        # 1. GESTIÓN DE REACCIONES (Tu lógica original intacta)
        if 'reaction' in msg:
            emoji = msg['reaction'].get('emoji')
            if emoji in ["💖", "⭐", "💎"]:
                ai_utils.set_user_state(phone, f"ESPERANDO_CAPTURE_{emoji}")
                whatsapp_utils.send_whatsapp_message(phone, f"Has elegido {emoji}. Envía el capture para verificar.")
                return {"status": "ok"}

        # 2. GESTIÓN DE TEXTO EN CADENA (Optimizado en Segundo Plano)
        if 'text' in msg:
            texto = msg['text']['body']
            texto_limpio = ai_utils.normalizar_texto(texto)
            
            supabase = get_supabase()
            reglas_encontradas = []
            
            # Buscamos todas las reglas creadas que coincidan con la palabra clave ingresada
            try:
                reglas_bd = supabase.table("clientes").select("palabra_clave, respuesta_id").execute().data
                for r in reglas_bd:
                    if ai_utils.normalizar_texto(r['palabra_clave']) == texto_limpio:
                        reglas_encontradas.append(r)
            except Exception as e:
                print(f"Error buscando reglas en la Base de Datos: {e}")

            if reglas_encontradas:
                # ENVIAMOS LA CARGA MULTIMEDIA AL SEGUNDO PLANO Y LIBERAMOS AL SERVIDOR DE INMEDIATO
                background_tasks.add_task(enviar_cadena_mensajes, phone, reglas_encontradas)
                return {"status": "ok"}
            else:
                # Si no coincide la palabra clave, responde tu Inteligencia Artificial de Gemini
                respuesta_ia = ai_utils.generar_respuesta_ia(texto)
                whatsapp_utils.send_whatsapp_message(phone, respuesta_ia)

        # 3. GESTIÓN DE IMÁGENES (Verificación de Pagos - Tu lógica original intacta)
        elif 'image' in msg:
            estado = ai_utils.get_user_state(phone)
            if estado.startswith("ESPERANDO_CAPTURE_"):
                emoji_usado = estado.split("_")[2]
                monto = ai_utils.obtener_monto_por_emoji(emoji_usado)
                
                # Procesamiento binario de imágenes
                img_bytes = whatsapp_utils.get_image_from_meta(msg['image']['id'])
                cfg = ai_utils.obtener_datos_verificacion()
                
                # Validación con Gemini
                res = ai_utils.verificar_pago_movil(img_bytes, cfg['cedula_esperada'], cfg['telefono_esperado'], monto)
                whatsapp_utils.send_whatsapp_message(phone, res)
                
                # Persistencia de transacciones
                ai_utils.save_to_db(phone, res, url_path=msg['image']['id'])
                ai_utils.set_user_state(phone, "IDLE")
            else:
                whatsapp_utils.send_whatsapp_message(phone, "No estoy esperando un capture tuyo en este momento.")

    except Exception as e:
        print(f"Error crítico en la ejecución del Webhook: {e}")
        
    return {"status": "ok"}
