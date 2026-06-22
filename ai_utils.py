import os
import io
import PIL.Image
import unicodedata
import google.generativeai as genai
from supabase import create_client

# Configuración
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def normalizar_texto(texto):
    texto = texto.lower()
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')

def buscar_respuesta_automatica(texto_usuario):
    """Consulta la base de datos relacional (palabras_clave -> respuestas)."""
    texto_limpio = normalizar_texto(texto_usuario)
    try:
        # Buscamos todas las reglas
        reglas = supabase.table("palabras_clave").select("keyword, respuesta_id").execute().data
        
        for r in reglas:
            if normalizar_texto(r['keyword']) in texto_limpio:
                # Obtenemos la respuesta asociada
                resp = supabase.table("respuestas").select("contenido").eq("id", r['respuesta_id']).execute().data
                if resp:
                    return resp[0]['contenido']
    except Exception as e:
        print(f"Error en búsqueda: {e}")
    return None

def verificar_pago_movil(img_bytes, cedula, telefono):
    """Audita el comprobante de pago."""
    img = PIL.Image.open(io.BytesIO(img_bytes))
    prompt = f"Auditor de pagos. Datos esperados: Cédula {cedula}, Teléfono {telefono}. Responde: ✅ PAGO VERIFICADO o ❌ PAGO RECHAZADO."
    return model.generate_content([prompt, img]).text

def obtener_datos_verificacion():
    res = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
    return res.data[0] if res.data else {"cedula_esperada": "0", "telefono_esperado": "0"}

def save_to_db(phone, response, text=None, url_path=None):
    try:
        supabase.table("mensajes").insert({
            "phone": phone, 
            "texto": text, 
            "url_archivo": url_path, 
            "respuesta": response
        }).execute()
    except Exception as e:
        print(f"Error al guardar: {e}")
