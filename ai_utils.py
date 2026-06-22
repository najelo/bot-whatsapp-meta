import os
import io
import PIL.Image
import google.generativeai as genai
from supabase import create_client

# Configuración inicial
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def verificar_pago_movil(img_bytes, cedula, telefono):
    """Audita el comprobante de pago."""
    img = PIL.Image.open(io.BytesIO(img_bytes))
    prompt = f"Eres un auditor. Datos esperados: Cédula {cedula}, Teléfono {telefono}. Responde: ✅ PAGO VERIFICADO o ❌ PAGO RECHAZADO."
    return model.generate_content([prompt, img]).text

def obtener_datos_verificacion():
    """Trae los datos de pago activos."""
    res = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
    return res.data[0] if res.data else {"cedula_esperada": "0", "telefono_esperado": "0"}

def buscar_respuesta_automatica(texto):
    """Consulta la tabla 'respuestas_automaticas'."""
    try:
        reglas = supabase.table("respuestas_automaticas").select("*").execute().data
        for r in reglas:
            if r['palabra_clave'].lower() in texto.lower():
                return r['respuesta_texto']
    except Exception as e:
        print(f"Error buscando FAQ: {e}")
    return None

def responder_pregunta_usuario(pregunta):
    """Consulta la 'informacion_negocio' mediante IA."""
    try:
        res = supabase.table("informacion_negocio").select("contenido").execute()
        datos = "\n".join([r['contenido'] for r in res.data]) if res.data else "Sin datos adicionales."
        
        prompt = f"""
        Información oficial de la empresa:
        {datos}
        
        Pregunta del usuario: {pregunta}
        
        Reglas estrictas:
        - Usa solo la información oficial para responder.
        - Si no tienes la respuesta, responde: "Lo siento, no dispongo de esa información. Por favor, contacta con un administrador."
        """
        return model.generate_content(prompt).text
    except Exception as e:
        print(f"Error en IA: {e}")
        return "Lo siento, hubo un error técnico. Contacta con un administrador."

def save_to_db(phone, response, text=None, url_path=None):
    """Registra en historial."""
    try:
        supabase.table("mensajes").insert({
            "phone": phone, 
            "texto": text, 
            "url_archivo": url_path, 
            "respuesta": response
        }).execute()
    except Exception as e:
        print(f"Error al guardar en BD: {e}")
