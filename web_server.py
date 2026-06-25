import os
import time
from fastapi import FastAPI, Request, Response, BackgroundTasks
import ai_utils
import whatsapp_utils

app = FastAPI()

# Token de verificación para configurar el Webhook en el panel de Meta Developers
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "tu_token_secreto_aqui")

def enviar_respuestas_secuenciales(phone: str, respuestas_lista: list):
    """
    Ejecuta el envío de ráfagas de mensajes en cadena en segundo plano.
    Evita bloqueos y valida si la respuesta viene como texto plano o diccionario.
    """
    for resp in respuestas_lista:
        if isinstance(resp, str):
            contenido = resp
            tipo = "texto"
        elif isinstance(resp, dict):
            contenido = resp.get("contenido")
            tipo = resp.get("tipo_contenido", "texto")
        else:
            continue
            
        if tipo == "texto":
            whatsapp_utils.send_whatsapp_message(phone, contenido)
        elif tipo == "documento":
            whatsapp_utils.send_whatsapp_document(phone, contenido, "Documento.pdf")
        elif tipo == "multimedia":
            whatsapp_utils.send_whatsapp_image(phone, contenido)
        elif tipo == "audio":
            whatsapp_utils.send_whatsapp_audio(phone, contenido)
            
        time.sleep(1.5)

def procesar_verificacion_pago_bg(phone: str, image_bytes: bytes, monto_esperado: float):
    """
    Procesa la imagen con Gemini en segundo plano para evitar reenvíos de Meta.
    """
    try:
        exito, respuesta_ia = ai_utils.verificar_capture_con_gemini(image_bytes, monto_esperado)
        
        if exito:
            whatsapp_utils.send_whatsapp_message(phone, f"✅ Pago verificado con éxito:\n\n{respuesta_ia}")
            ai_utils.set_user_state(phone, "INICIO")
        else:
            whatsapp_utils.send_whatsapp_message(phone, f"❌ {respuesta_ia}")
            
    except Exception as e:
        print(f"❌ Error en la verificación en segundo plano: {e}")
        whatsapp_utils.send_whatsapp_message(phone, "⚠️ Ocurrió un error interno al procesar tu imagen de pago.")

@app.get("/webhook")
async def verificar_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == WEBHOOK_VERIFY_TOKEN:
            return Response(content=challenge, media_type="text/plain")
    return Response(content="Forbidden", status_code=403)

@app.post("/webhook")
async def recibir_notificacion(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return "OK", 200

        msg = messages[0]
        phone = msg.get("from")
        
        # Consultamos el estado actual del usuario en la tabla 'estados_usuario'
        estado = ai_utils.get_user_state(phone)

        # =====================================================================
        # FILTRAR SEGÚN EL ESTADO PRIMERO
        # =====================================================================
        if estado and estado.startswith("ESPERANDO_CAPTURE_"):
            if msg.get("type") == "image":
                emoji_usado = estado.split("_")[2]
                monto_esperado = ai_utils.obtener_monto_por_emoji(emoji_usado)
                
                image_id = msg["image"]["id"]
                image_url = whatsapp_utils.get_media_url(image_id)
                
                if image_url:
                    image_bytes = whatsapp_utils.download_media(image_url)
                    background_tasks.add_task(procesar_verificacion_pago_bg, phone, image_bytes, monto_esperado)
                else:
                    whatsapp_utils.send_whatsapp_message(phone, "❌ No se pudo descargar la imagen de los servidores de Meta.")
                return "OK", 200
            else:
                whatsapp_utils.send_whatsapp_message(
                    phone, 
                    "⚠️ Tienes una verificación de pago pendiente.\nPor favor, envía únicamente la imagen del capture de tu Pago Móvil para continuar."
                )
                return "OK", 200

        # =====================================================================
        # CASO B: EL USUARIO ESTÁ LIBRE
        # =====================================================================
        if msg.get("type") == "reaction":
            emoji = msg["reaction"].get("emoji")
            ai_utils.set_user_state(phone, f"ESPERANDO_CAPTURE_{emoji}")
            whatsapp_utils.send_whatsapp_message(phone, f"Has elegido {emoji}. Envía el capture de tu pago para verificar.")
            return "OK", 200

        if msg.get("type") == "text":
            texto_usuario = msg["text"]["body"].strip()
            respuestas_encontradas = ai_utils.buscar_todas_las_respuestas(texto_usuario)
            
            if respuestas_encontradas:
                background_tasks.add_task(enviar_respuestas_secuenciales, phone, respuestas_encontradas)
            else:
                whatsapp_utils.send_whatsapp_message(
                    phone, 
                    "Hola. Reacciona con un emoji a nuestros mensajes para iniciar el proceso de verificación de pago."
                )
            return "OK", 200

        if msg.get("type") == "audio":
            audio_id = msg["audio"]["id"]
            audio_url = whatsapp_utils.get_media_url(audio_id)
            audio_bytes = whatsapp_utils.download_media(audio_url)
            
            texto_transcrito = ai_utils.transcribir_audio_con_whisper(audio_bytes)
            if texto_transcrito:
                respuestas_encontradas = ai_utils.buscar_todas_las_respuestas(texto_transcrito)
                if respuestas_encontradas:
                    background_tasks.add_task(enviar_respuestas_secuenciales, phone, respuestas_encontradas)
            return "OK", 200

    except Exception as e:
        print(f"❌ Error procesando el webhook de Meta: {e}")
        
    return "OK", 200
