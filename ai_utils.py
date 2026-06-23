import os
import io
import re
import unicodedata
import PIL.Image
import google.generativeai as genai
from supabase import create_client

# --- Configuración Inicial ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def normalizar_texto(texto):
    """Limpia el texto para facilitar la comparación de palabras clave."""
    # 1. Pasar a minúsculas
    texto = texto.lower()
    # 2. Eliminar tildes
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    # 3. Eliminar caracteres especiales (puntuación, símbolos)
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    # 4. Eliminar espacios extra
    return texto.strip()

def buscar_respuesta_automatica(texto_usuario):
    """Busca una respuesta en Supabase y devuelve SOLO LA PRIMERA coincidencia."""
    texto_limpio = normalizar_texto(texto_usuario)
    
    try:
        # Consultamos las reglas de palabras clave
        reglas = supabase.table("clientes").select("palabra_clave, respuesta_id").execute().data
        
        for r in reglas:
            # Normalizamos la palabra clave almacenada
            kw = normalizar_texto(r['palabra_clave'])
            
            # Comparamos si la palabra clave existe en el mensaje
            if kw in texto_limpio:
                # Buscamos el contenido de la respuesta
                resp = supabase.table("respuestas").select("contenido").eq("id", r['respuesta_id']).execute().data
                if resp:
                    # RETORNO INMEDIATO: Detiene el bucle y evita envíos múltiples
                    return resp[0]['contenido']
                    
    except Exception as e:
        print(f"Error al consultar la base de datos: {e}")
        
    return None

def verificar_pago_movil(img_bytes, cedula, telefono):
    """Audita el comprobante de pago usando Gemini."""
    try:
        img = PIL.Image.open(io.BytesIO(img_bytes))
        prompt = f"Auditor de pagos. Datos esperados: Cédula {cedula}, Teléfono {telefono}. Responde: ✅ PAGO VERIFICADO o ❌ PAGO RECHAZADO."
        return model.generate_content([prompt, img]).text
    except Exception as e:
        return f"Error en la verificación: {str(e)}"

def obtener_datos_verificacion():
    """Obtiene los datos de pago activos del administrador."""
    try:
        res = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
        return res.data[0] if res.data else {"cedula_esperada": "0", "telefono_esperado": "0"}
    except:
        return {"cedula_esperada": "0", "telefono_esperado": "0"}

def save_to_db(phone, response, text=None, url_path=None):
    """Guarda el historial de mensajes en Supabase."""
    try:
        supabase.table("mensajes").insert({
            "phone": phone, 
            "texto": text, 
            "url_archivo": url_path, 
            "respuesta": response
        }).execute()
    except Exception as e:
        print(f"Error al guardar registro en BD: {e}")
