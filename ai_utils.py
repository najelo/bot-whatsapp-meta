import os
# Importación del nuevo SDK oficial de Google que reemplaza a google-generativeai
from google import genai
from google.genai import types
from auth_utils import get_supabase  # Conector para tu base de datos Supabase

def verificar_capture_con_gemini(image_bytes: bytes, monto_esperado: float):
    """
    Verifica un capture de pantalla de Pago Móvil o transferencia usando 
    el nuevo SDK oficial 'google-genai' y el modelo rápido 'gemini-2.5-flash'.
    """
    try:
        # El cliente detecta de forma automática la variable de entorno GEMINI_API_KEY
        client = genai.Client()
        
        # Preparamos los bytes de la imagen con el nuevo formato 'types.Part'
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
        MENSAJE: Un resumen corto en español de lo verificado (Ej: Pago confirmado por {monto_esperado} Bs.)
        """
        
        # Llamada al modelo con la nueva sintaxis unificada de Google
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[imagen_ia, prompt]
        )
        
        texto_ia = response.text
        print(f"🤖 Respuesta cruda de Gemini: {texto_ia}")
        
        # Validación de éxito basada en la respuesta del modelo
        if "EXITO: True" in texto_ia:
            return True, texto_ia
        else:
            return False, texto_ia
            
    except Exception as e:
        print(f"❌ Error en ai_utils usando el nuevo SDK de Gemini: {e}")
        return False, f"Error al verificar con el motor de IA: {str(e)}"


# =====================================================================
# GESTIÓN DE ESTADOS Y REGLAS EN SUPABASE (Corregido para nuevas versiones)
# =====================================================================

def get_user_state(phone: str) -> str:
    """Obtiene el estado actual del flujo del usuario desde Supabase."""
    try:
        supabase = get_supabase()
        # CORREGIDO: Usamos .execute() de forma segura en lugar de .maybe_execute()
        res = supabase.table("estados_usuarios").select("estado").eq("telefono", phone).execute()
        
        # Verificamos si la lista tiene datos antes de acceder al índice [0]
        if res and res.data and len(res.data) > 0:
            return res.data[0].get("estado", "INICIO")
            
        return "INICIO"
    except Exception as e:
        print(f"❌ Error obteniendo estado en ai_utils: {e}")
        return "INICIO"

def set_user_state(phone: str, nuevo_estado: str):
    """Actualiza o inserta el estado del flujo de un usuario en Supabase."""
    try:
        supabase = get_supabase()
        # Hacemos un upsert para registrar o cambiar el estado (ej: ESPERANDO_CAPTURE_💸)
        supabase.table("estados_usuarios").upsert({"telefono": phone, "estado": nuevo_estado}).execute()
    except Exception as e:
        print(f"❌ Error guardando estado en ai_utils: {e}")

def obtener_monto_por_emoji(emoji: str) -> float:
    """Mapea el emoji seleccionado por el usuario con el precio del recetario/producto."""
    mapa_precios = {
        "💖": 150.00,
        "💸": 200.00,
        "🔥": 350.00,
        "💳": 500.00
    }
    return mapa_precios.get(emoji, 0.00)

def buscar_todas_las_respuestas(texto_usuario: str) -> list:
    """
    Busca palabras clave en Supabase y devuelve la lista de respuestas 
    (ya sean textos o paths a archivos en Storage).
    """
    try:
        supabase = get_supabase()
        texto_limpio = texto_usuario.lower().strip()
        
        # Consulta en tu tabla de clientes/reglas por palabra clave
        res = supabase.table("clientes").select("id, palabra_clave, respuestas(id, contenido, tipo_contenido)").execute()
        
        respuestas_encontradas = []
        if res and res.data:
            for regla in res.data:
                palabra_regla = regla.get("palabra_clave", "").lower().strip()
                # Si la palabra clave coincide o está dentro del mensaje del usuario
                if palabra_regla in texto_limpio and regla.get("respuestas"):
                    respuestas_encontradas.append(regla["respuestas"])
                    
        return respuestas_encontradas
    except Exception as e:
        print(f"❌ Error buscando respuestas: {e}")
        return []

def transcribir_audio_con_whisper(audio_bytes: bytes) -> str:
    """
    Procesador de notas de voz.
    """
    try:
        return ""
    except Exception as e:
        print(f"❌ Error transcribiendo audio: {e}")
        return ""
