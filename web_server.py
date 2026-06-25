import os
import time
from fastapi import FastAPI, Request, Response, BackgroundTasks
import ai_utils
import whatsapp_utils

app = FastAPI()

# Token de verificación para configurar el Webhook en Meta Developers
WEBHOOK_VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN", "tu_token_secreto_aqui")

def enviar_respuestas_secuenciales(phone: str, respuestas_lista: list):
    """
    Ejecuta el bucle de envío en segundo plano. Esto evita que Meta 
    asuma que el servidor está caído y duplique/triplique los mensajes.
    """
    for resp in respuestas_lista:
        contenido = resp.get("contenido")
        tipo = resp.get("tipo_contenido", "texto")
        
        if tipo == "texto":
            whatsapp_utils.send_whatsapp_message(phone, contenido)
        elif tipo == "documento":
            whatsapp_utils.send_whatsapp_document(phone, contenido, "Documento.pdf")
        elif tipo == "multimedia":
            whatsapp_utils.send_whatsapp_image(phone, contenido)
        elif tipo == "audio":
            whatsapp_utils.send_whatsapp_audio(phone, contenido)
            
        # Pausa de cortesía entre mensajes de la cadena
        time.sleep(1.5)

@app.get("/webhook")
async def verificar_webhook(request: Request):
    """Validación obligatoria del Webhook que exige Meta."""
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
    """Procesamiento centralizado de eventos de WhatsApp Cloud API."""
    try:
        body = await request.json()
        
        # Estructura básica de Meta
        entry = body.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return "OK", 200

        msg = messages[0]
        phone = msg.get("from")
        
        # 1. Identificar el estado actual del usuario en la Base de Datos
        estado = ai_utils.get_user_state(phone)

        # ==========================================
        # CASO A: EL BOT ESTÁ ESPERANDO UN CAPTURE
        # ==========================================
        if estado and estado.startswith("ESPERANDO_CAPTURE_"):
            # Si envía una imagen, procesamos el pago de inmediato con tu lógica
            if msg.get("type") == "image":
                emoji_usado = estado.split("_")[2]
                monto_esperado = ai_utils.obtener_monto_por_emoji(emoji_usado)
                
                image_id = msg["image"]["id"]
                image_url = whatsapp_utils.get_media_url(image_id)
                image_bytes = whatsapp_utils.download_media(image_url)
                
                # Tu validación nativa con Gemini API
                exito, respuesta_ia = ai_utils.verificar_capture_con_gemini(image_bytes, monto_esperado)
                
                if exito:
                    whatsapp_utils.send_whatsapp_message(phone, f"✅ Pago verificado con éxito:\n\n{respuesta_ia}")
                    ai_utils.set_user_state(phone, "INICIO")  # Liberamos el estado
                else:
                    whatsapp_utils.send_whatsapp_message(phone, f"❌ {respuesta_ia}")
                return "OK", 200

            # SI ENVÍA TEXTO O AUDIO MIENTRAS SE ESPERA EL PAGO, SE BLOQUEA Y SE LE RECUERDA EL CAPTURE
            else:
                whatsapp_utils.send_whatsapp_message(
                    phone, 
                    "⚠️ Tienes una verificación de pago pendiente.\nPor favor, envía la imagen del capture de tu Pago Móvil para continuar."
                )
                return "OK", 200

        # ==========================================
        # CASO B: FLUJO NORMAL (BOT LIBRE O INICIO)
        # ==========================================
        # 2. Si el usuario reacciona con un Emoji a un mensaje (Iniciador de Pago)
        if msg.get("type") == "reaction":
            emoji = msg["reaction"].get("emoji")
            # Registramos que ahora esperamos la foto para ese emoji específico
            ai_utils.set_user_state(phone, f"ESPERANDO_CAPTURE_{emoji}")
            whatsapp_utils.send_whatsapp_message(phone, f"Has elegido {emoji}. Envía el capture de tu pago para verificar.")
            return "OK", 200

        # 3. Si el usuario envía un mensaje de texto plano
        if msg.get("type") == "text":
            texto_usuario = msg["text"]["body"].strip()
            
            # Buscamos en Supabase si la palabra clave activa una cadena de respuestas
            respuestas_encontradas = ai_utils.buscar_todas_las_respuestas(texto_usuario)
            
            if respuestas_encontradas:
                # Se delega al BackgroundTask para responder al instante a Meta con un 200 OK
                background_tasks.add_task(enviar_respuestas_secuenciales, phone, respuestas_encontradas)
            else:
                # Mensaje por defecto si no coincide ninguna regla
                whatsapp_utils.send_whatsapp_message(
                    phone, 
                    "No estoy esperando un pago. Reacciona con un emoji para iniciar o escribe una palabra clave válida."
                )
            return "OK", 200

        # 4. Si el usuario envía una nota de voz (Transcripción asíncrona)
        if msg.get("type") == "audio":
            audio_id = msg["audio"]["id"]
            audio_url = whatsapp_utils.get_media_url(audio_id)
            audio_bytes = whatsapp_utils.download_media(audio_url)
            
            # Ejecutamos tu transcripción nativa en la que estás trabajando
            texto_transcrito = ai_utils.transcribir_audio_con_whisper(audio_bytes)
            
            if texto_transcrito:
                respuestas_encontradas = ai_utils.buscar_todas_las_respuestas(texto_transcrito)
                if respuestas_encontradas:
                    background_tasks.add_task(enviar_respuestas_secuenciales, phone, respuestas_encontradas)
            return "OK", 200

    except Exception as e:
        print(f"Error procesando el webhook de Meta: {e}")
        
    return "OK", 200
