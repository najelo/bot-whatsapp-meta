import os
import io
import PIL.Image
import unicodedata
import google.generativeai as genai
from supabase import create_client
import re

# Configuración
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def normalizar_texto(texto):
    texto = texto.lower()
    texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8')
    # Eliminamos solo caracteres especiales que puedan interferir, pero mantenemos la estructura
    return texto.strip()

def buscar_respuesta_automatica(texto_usuario):
    texto_limpio = normalizar_texto(texto_usuario)
    lista_respuestas = [] 
    
    try:
        reglas = supabase.table("clientes").select("palabra_clave, respuesta_id").execute().data
        
        for r in reglas:
            kw = normalizar_texto(r['palabra_clave'])
            if kw in texto_limpio:
                resp = supabase.table("respuestas").select("contenido").eq("id", r['respuesta_id']).execute().data
                if resp:
                    lista_respuestas.append(resp[0]['contenido'])
    except Exception as e:
        print(f"Error en BD: {e}")
    
    # Retornamos la lista completa (si no encuentra nada, será una lista vacía [])
    return lista_respuestas

def verificar_pago_movil(img_bytes, cedula, telefono):
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
