import os
import io
import PIL.Image
import google.generativeai as genai
from supabase import create_client

# Configuración
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Usamos 1.5-flash por ser el estándar más estable para multimodalidad
model = genai.GenerativeModel('gemini-3.5-flash')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def process_text(text):
    """Procesa mensajes de texto normales."""
    return model.generate_content(text).text

def process_image(img_bytes):
    """Describe una imagen si no es un pago."""
    img = PIL.Image.open(io.BytesIO(img_bytes))
    return model.generate_content(["Describe esta imagen:", img]).text

def verificar_pago_movil(img_bytes, cedula_esperada, telefono_esperado):
    """
    Analiza una imagen buscando datos específicos de pago móvil.
    Retorna un string con el resultado del análisis.
    """
    img = PIL.Image.open(io.BytesIO(img_bytes))
    
    prompt = f"""
    Eres un verificador de pagos móviles. Analiza la imagen del comprobante y extrae:
    1. Número de cédula/RIF.
    2. Número de teléfono.
    
    Compara si los datos extraídos coinciden exactamente con:
    - Cédula esperada: {cedula_esperada}
    - Teléfono esperado: {telefono_esperado}
    
    Responde solo con:
    - "PAGO VERIFICADO" si ambos coinciden.
    - "DATOS INCORRECTOS: [motivo]" si no coinciden.
    - "NO SE PUDIERON LEER LOS DATOS" si la imagen no es clara.
    """
    
    response = model.generate_content([prompt, img])
    return response.text

def save_to_db(phone, response, text=None, url_path=None):
    """Guarda el historial de la interacción en Supabase."""
    supabase.table("mensajes").insert({
        "phone": phone, 
        "texto": text, 
        "url_archivo": url_path, 
        "respuesta": response
    }).execute()

def obtener_datos_verificacion():
    """Trae de la base de datos los parámetros actuales de pago."""
    # Asumiendo que tu tabla en Supabase se llama 'configuracion_pago'
    # y tiene una fila activa
    response = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
    if response.data:
        return response.data[0]
    return None
