import os
import io
import time
import PIL.Image
import unicodedata
import re
import google.generativeai as genai
from auth_utils import get_supabase

# Configuración de Gemini (SDK estándar compatible con tus dependencias)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def normalizar_texto(texto):
    """Limpia el texto quitando acentos y caracteres especiales."""
    texto = unicodedata.normalize('NFD', texto.lower()).encode('ascii', 'ignore').decode('utf-8')
    return re.sub(r'[^a-z0-9\s]', '', texto).strip()

def obtener_monto_por_emoji(emoji: str) -> float:
    """Mapea el emoji seleccionado por el usuario con el precio original de negocio."""
    mapa_precios = {
        "💖": 3300.0,
        "⭐": 20.0,
        "💎": 10.0
    }
    return mapa_precios.get(emoji, 0.00)

def buscar_todas_las_respuestas(texto_usuario: str) -> list:
    """
    Busca respuestas automatizadas por palabras clave en Supabase.
    Mantiene intacta tu estructura original de joins para extraer contenido y tipo_contenido (PDF/multimedia).
    """
    try:
        supabase = get_supabase()
        texto_limpio = texto_usuario.lower().strip()
        # Tu query exacta con la relación de la tabla respuestas
        res = supabase.table("clientes").select("id, palabra_clave, respuestas(id, contenido, tipo_contenido)").execute()
        
        respuestas_encontradas = []
        if res and res.data:
            for regla in res.data:
                palabra_regla = regla.get("palabra_clave", "").lower().strip()
                if palabra_regla in texto_limpio:
                    datos_respuesta = regla.get("respuestas")
                    if datos_respuesta:
                        respuestas_encontradas.append({
                            "contenido": datos_respuesta.get("contenido"),
                            "tipo_contenido": datos_respuesta.get("tipo_contenido", "texto")
                        })
        return respuestas_encontradas
    except Exception as e:
        print(f"❌ Error buscando respuestas en ai_utils: {e}")
        return []

def generar_respuesta_ia(texto_usuario):
    """Genera respuestas conversacionales cuando el texto no coincide con palabras clave."""
    try:
        prompt = f"Eres un asistente de atención al cliente automatizado. Responde de forma amable y concisa a: {texto_usuario}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "Hola. Reacciona con un emoji a nuestros mensajes para iniciar el proceso de verificación de pago."

def verificar_pago_movil(img_bytes, cedula, telefono, monto_minimo):
    """
    Verifica el capture de Pago Móvil con reintentos inteligentes 
    para absorber errores de saturación 503 de los servidores de Google.
    """
    intentos_maximos = 3
    espera = 2  # Segundos iniciales de pausa antes del reintento

    for intento in range(intentos_maximos):
        try:
            img = PIL.Image.open(io.BytesIO(img_bytes))
            prompt = (f"Auditor de pagos estricto. Datos esperados en el recibo: Cédula {cedula}, Teléfono {telefono}. "
                      f"Monto exacto exigido: {monto_minimo}. Analiza detenidamente la imagen: "
                      "¿Coinciden los datos clave y el monto de la transferencia es igual o mayor al exigido? "
                      "Responde ÚNICAMENTE empezando con: ✅ PAGO VERIFICADO (seguido de un resumen muy breve) "
                      "o ❌ PAGO RECHAZADO (indicando qué dato falló).")
            
            response = model.generate_content([prompt, img])
            return response.text

        except Exception as e:
            if "503" in str(e) and intento < intentos_maximos - 1:
                print(f"⚠️ Servidor saturado (503). Reintentando en {espera}s... (Intento {intento + 1}/{intentos_maximos})")
                time.sleep(espera)
                espera *= 2  # Aumento exponencial del tiempo
            else:
                print(f"❌ Error crítico final en verificar_pago_movil: {e}")
                return "❌ Error transitorio del sistema (Código 503). Por favor, intenta enviar tu capture nuevamente en unos instantes."

def verificar_capture_con_gemini(image_bytes: bytes, monto_esperado: float):
    """
    Función puente/alias para mantener compatibilidad con las llamadas 
    en segundo plano (background tasks) que invoca tu web_server.py.
    """
    cfg = obtener_datos_verificacion()
    resultado_texto = verificar_pago_movil(
        img_bytes=image_bytes, 
        cedula=cfg['cedula_esperada'], 
        telefono=cfg['telefono_esperado'], 
        monto_minimo=monto_esperado
    )
    
    if "✅ PAGO VERIFICADO" in resultado_texto:
        return True, resultado_texto
    else:
        return False, resultado_texto

def obtener_datos_verificacion():
    """Obtiene los datos del receptor activo desde la configuración de pago."""
    try:
        supabase = get_supabase()
        res = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
        return res.data[0] if res.data else {"cedula_esperada": "0", "telefono_esperado": "0"}
    except Exception as e:
        print(f"❌ Error al obtener datos de verificación: {e}")
        return {"cedula_esperada": "0", "telefono_esperado": "0"}

def set_user_state(phone: str, nuevo_estado: str):
    """Guarda o actualiza el estado usando la columna 'phone'."""
    try:
        supabase = get_supabase()
        supabase.table("estados_usuario").upsert({"phone": phone, "estado": nuevo_estado}).execute()
    except Exception as e:
        print(f"❌ Error guardando estado en ai_utils: {e}")

def get_user_state(phone: str) -> str:
    """Consulta el estado actual de la conversación de un usuario."""
    try:
        supabase = get_supabase()
        res = supabase.table("estados_usuario").select("estado").eq("phone", phone).execute()
        return res.data[0]["estado"] if res and res.data else "IDLE"
    except Exception as e:
        print(f"❌ Error obteniendo estado en ai_utils: {e}")
        return "IDLE"

def save_to_db(phone, response, text=None, url_path=None):
    """Guarda el log del mensaje procesado en el historial."""
    try:
        supabase = get_supabase()
        data = {"phone": phone, "respuesta": response}
        if text: data["texto_usuario"] = text
        if url_path: data["url_imagen"] = url_path
        supabase.table("historial_mensajes").insert(data).execute()
    except Exception as e:
        print(f"❌ Error guardando historial: {e}")
