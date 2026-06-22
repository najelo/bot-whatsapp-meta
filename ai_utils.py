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

import re # Asegúrate de importar esto al principio

def normalizar_texto(texto):
    # 1. Pasar a minúsculas
    texto = texto.lower()
    # 2. Eliminar tildes
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    # 3. Eliminar todo lo que NO sea letra o número (aquí eliminamos los signos de interrogación, exclamación, puntos, etc.)
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    # 4. Eliminar espacios extra al inicio o final
    return texto.strip()

def buscar_respuesta_automatica(texto_usuario):
    # El texto del usuario llega limpio (sin ? ! . tildes)
    texto_limpio = normalizar_texto(texto_usuario)
    
    try:
        reglas = supabase.table("clientes").select("palabra_clave, respuesta_id").execute().data
        
        for r in reglas:
            # Normalizamos también la palabra clave de la base de datos
            kw = normalizar_texto(r['palabra_clave'])
            
            # Ahora, si el usuario escribe: "¿Qué horario tienen?"
            # texto_limpio será: "que horario tienen"
            # y el código encontrará "horario" dentro de esa frase.
            if kw in texto_limpio:
                resp = supabase.table("respuestas").select("contenido").eq("id", r['respuesta_id']).execute().data
                if resp:
                    return resp[0]['contenido']
    except Exception as e:
        print(f"Error en BD: {e}")
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
