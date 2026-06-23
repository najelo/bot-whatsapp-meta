import os
import io
import PIL.Image
import unicodedata
import re
import google.generativeai as genai
from supabase import create_client

# Configuración
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def normalizar_texto(texto):
    """Limpia el texto eliminando tildes y caracteres especiales."""
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return texto.strip()

def buscar_todas_las_respuestas(texto_usuario):
    """Busca todas las respuestas asociadas a una palabra clave."""
    texto_limpio = normalizar_texto(texto_usuario)
    lista_respuestas = []
    
    try:
        reglas = supabase.table("clientes").select("palabra_clave, respuesta_id").execute().data
        for r in reglas:
            if normalizar_texto(r['palabra_clave']) in texto_limpio:
                resp = supabase.table("respuestas").select("contenido").eq("id", r['respuesta_id']).execute().data
                if resp:
                    lista_respuestas.append(resp[0]['contenido'])
    except Exception as e:
        print(f"Error en BD buscando todas las respuestas: {e}")
    
    return lista_respuestas

def verificar_pago_movil(img_bytes, cedula, telefono):
    """Audita el comprobante de pago."""
    img = PIL.Image.open(io.BytesIO(img_bytes))
    prompt = f"Auditor de pagos. Datos esperados: Cédula {cedula}, Teléfono {telefono}. Responde: ✅ PAGO VERIFICADO o ❌ PAGO RECHAZADO."
    return model.generate_content([prompt, img]).text

def obtener_datos_verificacion():
    """Obtiene los datos configurados para verificar pagos."""
    res = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
    return res.data[0] if res.data else {"cedula_esperada": "0", "telefono_esperado": "0"}

def save_to_db(phone, response, text=None, url_path=None):
    """Guarda la interacción en la base de datos."""
    try:
        supabase.table("mensajes").insert({
            "phone": phone, 
            "texto": text, 
            "url_archivo": url_path, 
            "respuesta": response
        }).execute()
    except Exception as e:
        print(f"Error al guardar: {e}")
