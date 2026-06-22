import os
import io
import PIL.Image
import google.generativeai as genai
from supabase import create_client

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def verificar_pago_movil(img_bytes, cedula_esperada, telefono_esperado):
    img = PIL.Image.open(io.BytesIO(img_bytes))
    prompt = f"Eres un auditor. Datos esperados: Cédula {cedula_esperada}, Teléfono {telefono_esperado}. Responde: ✅ PAGO VERIFICADO o ❌ PAGO RECHAZADO."
    return model.generate_content([prompt, img]).text

def obtener_datos_verificacion():
    res = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
    return res.data[0] if res.data else None

def responder_pregunta_usuario(pregunta):
    # 1. Obtenemos toda la información oficial de la BD
    res = supabase.table("informacion_negocio").select("contenido").execute()
    datos_oficiales = str(res.data)
    
    # 2. Instrucción para Gemini
    prompt = f"""
    Información oficial: {datos_oficiales}
    Pregunta del usuario: {pregunta}
    
    Reglas:
    - Responde basándote ÚNICAMENTE en la información oficial.
    - Si la respuesta NO está ahí, responde: "Lo siento, no dispongo de esa información. Por favor, contacta con un administrador."
    - Sé breve y profesional.
    """
    return model.generate_content(prompt).text

def save_to_db(phone, response, text=None, url_path=None):
    supabase.table("mensajes").insert({"phone": phone, "texto": text, "url_archivo": url_path, "respuesta": response}).execute()
