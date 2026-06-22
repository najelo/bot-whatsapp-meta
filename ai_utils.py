import os
import io
import PIL.Image
import unicodedata
import google.generativeai as genai
from supabase import create_client

# Configuración
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def normalizar_texto(texto):
    """Elimina tildes y convierte a minúsculas para comparaciones precisas."""
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    return texto

def verificar_pago_movil(img_bytes, cedula, telefono):
    """Audita el comprobante de pago."""
    img = PIL.Image.open(io.BytesIO(img_bytes))
    prompt = f"Auditor de pagos. Datos esperados: Cédula {cedula}, Teléfono {telefono}. Responde: ✅ PAGO VERIFICADO o ❌ PAGO RECHAZADO."
    return model.generate_content([prompt, img]).text

def obtener_datos_verificacion():
    """Trae los datos de pago activos."""
    res = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
    return res.data[0] if res.data else {"cedula_esperada": "0", "telefono_esperado": "0"}

def buscar_respuesta_automatica(texto_usuario):
    """Consulta la tabla 'respuestas_automaticas' ignorando tildes y mayúsculas."""
    texto_limpio = normalizar_texto(texto_usuario)
    try:
        reglas = supabase.table("respuestas_automaticas").select("*").execute().data
        for r in reglas:
            if normalizar_texto(r['palabra_clave']) in texto_limpio:
                return r['respuesta_texto']
    except Exception as e:
        print(f"Error buscando FAQ: {e}")
    return None

def responder_pregunta_usuario(pregunta):
    """
    YA NO CONSULTA 'informacion_negocio'. 
    Si llega aquí es porque no encontró la respuesta en las FAQ.
    """
    return "Lo siento, no dispongo de esa información. Por favor, contacta con un administrador."

def save_to_db(phone, response, text=None, url_path=None):
    """Guarda el historial."""
    try:
        supabase.table("mensajes").insert({
            "phone": phone, 
            "texto": text, 
            "url_archivo": url_path, 
            "respuesta": response
        }).execute()
    except Exception as e:
        print(f"Error al guardar: {e}")
