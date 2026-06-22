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
    # 1. Buscamos la info del negocio
    res = supabase.table("informacion_negocio").select("contenido").execute()
    datos_oficiales = "\n".join([r['contenido'] for r in res.data]) if res.data else ""
    
    # 2. Si no hay ni FAQ ni Información, damos una respuesta estándar clara
    if not datos_oficiales:
        return "Lo siento, en este momento no cuento con información detallada para responder tu consulta. Por favor, contacta directamente con un administrador."
    
    # 3. Consulta a la IA con instrucción de no alucinar
    prompt = f"""
    Información oficial: {datos_oficiales}
    Pregunta del usuario: {pregunta}
    
    Reglas estrictas:
    - Responde basándote ÚNICAMENTE en la información oficial.
    - Si la respuesta NO está en la información oficial, responde EXACTAMENTE: 
      "Lo siento, no dispongo de esa información en mis registros. Por favor, contacta con un administrador."
    """
    return model.generate_content(prompt).text
    supabase.table("mensajes").insert({"phone": phone, "texto": text, "url_archivo": url_path, "respuesta": response}).execute()
