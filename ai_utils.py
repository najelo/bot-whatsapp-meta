import os
import io
import PIL.Image
import unicodedata
import re
import google.generativeai as genai
from auth_utils import get_supabase

# Inicialización segura usando auth_utils
supabase = get_supabase()

# Configuración de Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash')

def normalizar_texto(texto):
    texto = unicodedata.normalize('NFD', texto.lower()).encode('ascii', 'ignore').decode('utf-8')
    return re.sub(r'[^a-z0-9\s]', '', texto).strip()

# --- NUEVA FUNCIÓN CORREGIDA (Evita duplicados) ---
def buscar_respuesta_unica(texto_usuario):
    """Busca y retorna solo la primera coincidencia exacta."""
    texto_limpio = normalizar_texto(texto_usuario)
    try:
        reglas = supabase.table("clientes").select("palabra_clave, respuesta_id").execute().data
        for r in reglas:
            if normalizar_texto(r['palabra_clave']) == texto_limpio:
                resp = supabase.table("respuestas").select("contenido").eq("id", r['respuesta_id']).execute().data
                if resp:
                    return resp[0]['contenido']
    except Exception as e: 
        print(f"Error BD: {e}")
    return None

def generar_respuesta_ia(texto_usuario):
    """Respaldo para cuando no hay respuesta en la base de datos."""
    try:
        response = model.generate_content(f"Eres un asistente servicial. Responde a: {texto_usuario}")
        return response.text
    except Exception as e:
        return "Lo siento, no puedo procesar tu solicitud ahora mismo."

def obtener_monto_por_emoji(emoji):
    mapeo = {"💖": 3300.0, "⭐": 20.0, "💎": 10.0}
    return mapeo.get(emoji, 0.0)

def verificar_pago_movil(img_bytes, cedula, telefono, monto_minimo):
    try:
        img = PIL.Image.open(io.BytesIO(img_bytes))
        prompt = (f"Auditor de pagos. Datos esperados: Cédula {cedula}, Teléfono {telefono}. "
                  f"Monto mínimo exigido: {monto_minimo}. Analiza el capture: "
                  "¿Coinciden los datos y el monto es igual o mayor al mínimo? "
                  "Responde: ✅ PAGO VERIFICADO o ❌ PAGO RECHAZADO.")
        return model.generate_content([prompt, img]).text
    except Exception as e: return f"Error IA: {e}"

def obtener_datos_verificacion():
    res = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
    return res.data[0] if res.data else {"cedula_esperada": "0", "telefono_esperado": "0"}

def set_user_state(phone, state):
    supabase.table("estados_usuario").upsert({"phone": phone, "estado": state}).execute()

def get_user_state(phone):
    res = supabase.table("estados_usuario").select("estado").eq("phone", phone).execute()
    return res.data[0]['estado'] if res.data else "IDLE"

def save_to_db(phone, response, text=None, url_path=None):
    try:
        data = {"phone": phone, "respuesta": response}
        if text: data["texto_usuario"] = text
        if url_path: data["url_imagen"] = url_path
        supabase.table("historial_mensajes").insert(data).execute()
    except: pass
