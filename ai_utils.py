import os
from google import genai
from google.genai import types
from auth_utils import get_supabase

def verificar_capture_con_gemini(image_bytes: bytes, monto_esperado: float):
    """Verifica un capture usando el nuevo SDK 'google-genai'."""
    try:
        client = genai.Client()
        imagen_ia = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg"
        )
        
        prompt = f"""
        Analiza detalladamente esta imagen de un capture de transferencia o Pago Móvil.
        Determina si la transacción es válida y exitosa.
        El monto exacto que debes buscar, confirmar y validar es: {monto_esperado}
        
        Responde ESTRICTAMENTE en el siguiente formato:
        EXITO: True (o False si el monto no coincide, está borroso o es una transacción rechazada/pendiente)
        MENSAJE: Un resumen corto en español de lo verificado.
        """
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[imagen_ia, prompt]
        )
        
        texto_ia = response.text
        print(f"🤖 Respuesta cruda de Gemini: {texto_ia}")
        
        if "EXITO: True" in texto_ia:
            return True, texto_ia
        else:
            return False, texto_ia
            
    except Exception as e:
        print(f"❌ Error en ai_utils usando el nuevo SDK de Gemini: {e}")
        return False, f"Error al verificar con el motor de IA: {str(e)}"

def get_user_state(phone: str) -> str:
    """Obtiene el estado actual usando la columna 'phone'."""
    try:
        supabase = get_supabase()
        res = supabase.table("estados_usuario").select("estado").eq("phone", phone).execute()
        if res and res.data and len(res.data) > 0:
            return res.data[0].get("estado", "INICIO")
        return "INICIO"
    except Exception as e:
        print(f"❌ Error obteniendo estado en ai_utils: {e}")
        return "INICIO"

def set_user_state(phone: str, nuevo_estado: str):
    """Guarda o actualiza el estado usando la columna 'phone'."""
    try:
        supabase = get_supabase()
        supabase.table("estados_usuario").upsert({"phone": phone, "estado": nuevo_estado}).execute()
    except Exception as e:
        print(f"❌ Error guardando estado en ai_utils: {e}")

def obtener_monto_por_emoji(emoji: str) -> float:
    """Mapea el emoji seleccionado por el usuario con el precio."""
    mapa_precios = {
        "💖": 150.00,
        "💸": 200.00,
        "🔥": 350.00,
        "💳": 500.00
    }
    return mapa_precios.get(emoji, 0.00)

def buscar_todas_las_respuestas(texto_usuario: str) -> list:
    """Busca respuestas automatizadas por palabras clave."""
    try:
        supabase = get_supabase()
        texto_limpio = texto_usuario.lower().strip()
        res = supabase.table("clientes").select("id, palabra_clave, respuestas(id, contenido, tipo_contenido)").execute()
        
        respuestas_encontradas = []
        if res and res.data:
            for regla in res.data:
                palabra_regla = regla.get("palabra_clave", "").lower().strip()
                if palabra_regla in texto_limpio and regla.get("respuestas"):
                    respuestas_encontradas.append(regla["respuestas"])
        return respuestas_encontradas
    except Exception as e:
        print(f"❌ Error buscando respuestas: {e}")
        return []

def transcribir_audio_con_whisper(audio_bytes: bytes) -> str:
    return ""
