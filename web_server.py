import os
import requests
import google.generativeai as genai
from fastapi import FastAPI, Request
from dotenv import load_dotenv

load_dotenv() # Asegúrate de cargar tus variables de entorno
app = FastAPI()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash') # Verifica que la versión sea válida

# --- 1. Verificación del Webhook (Necesario para Meta) ---
@app.post("/webhook")
async def handle_message(request: Request):
    data = await request.json()
    
    try:
        entry = data.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        
        if 'messages' in value:
            message_data = value['messages'][0]
            phone_number = message_data['from']
            
            # --- NUEVA LÓGICA: Diferenciar texto de imagen ---
            if 'text' in message_data:
                # Caso mensaje de texto
                user_text = message_data['text']['body']
                response = model.generate_content(user_text)
                enviar_respuesta_whatsapp(phone_number, response.text)
            
            elif 'image' in message_data:
                # Caso mensaje de imagen
                # Aquí por ahora ignoramos la imagen o enviamos un mensaje de aviso
                enviar_respuesta_whatsapp(phone_number, "He recibido tu imagen, pero aún no puedo analizarla. ¡Envíame un texto!")
            
            else:
                print("Tipo de mensaje no soportado")
        
    except Exception as e:
        print(f"Error procesando: {e}")
        
    return {"status": "ok"}

def send_whatsapp_message(to, text):
    url = f"https://graph.facebook.com/v25.0/{os.getenv('PHONE_NUMBER_ID')}/messages"
    headers = {
        "Authorization": f"Bearer {os.getenv('ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"DEBUG: Meta respondió {response.status_code}: {response.text}")
