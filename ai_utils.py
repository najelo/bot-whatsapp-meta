import os
import io
import PIL.Image
import google.generativeai as genai
from supabase import create_client

# Configuración inicial
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def process_text(text):
    """Procesa mensajes de texto estándar con Gemini."""
    return model.generate_content(text).text

def buscar_respuesta_automatica(texto_usuario):
    """Consulta la tabla 'respuestas_automaticas' en Supabase."""
    reglas = supabase.table("respuestas_automaticas").select("*").execute().data
    for r in reglas:
        if r['palabra_clave'].lower() in texto_usuario.lower():
            return r['respuesta_texto']
    return None

def verificar_pago_movil(img_bytes, cedula_esperada, telefono_esperado):
    """Utiliza Gemini para auditar el comprobante bancario."""
    img = PIL.Image.open(io.BytesIO(img_bytes))
    prompt = f"""
    Eres un auditor financiero. Analiza este comprobante de pago móvil.
    Datos esperados: Cédula {cedula_esperada}, Teléfono {telefono_esperado}.
    Responde estrictamente:
    - "✅ PAGO VERIFICADO" si los datos coinciden.
    - "❌ PAGO RECHAZADO: Datos incorrectos" si no coinciden.
    - "⚠️ No se pudieron leer los datos" si la imagen es ilegible.
    """
    return model.generate_content([prompt, img]).text

def obtener_datos_verificacion():
    """Obtiene los parámetros activos de la base de datos."""
    res = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
    return res.data[0] if res.data else None

def save_to_db(phone, response, text=None, url_path=None):
    """Registra el historial de la interacción."""
    supabase.table("mensajes").insert({
        "phone": phone, 
        "texto": text, 
        "url_archivo": url_path, 
        "respuesta": response
    }).execute()
