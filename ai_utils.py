import os
import io
import time
import PIL.Image
import unicodedata
import re
import google.generativeai as genai
from supabase import create_client

# Configuración de Gemini (SDK estándar compatible con tus dependencias)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

# Inicialización directa de Supabase
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def normalizar_texto(texto):
    """Limpia el texto quitando acentos y caracteres especiales."""
    texto = unicodedata.normalize('NFD', texto.lower()).encode('ascii', 'ignore').decode('utf-8')
    return re.sub(r'[^a-z0-9\s]', '', texto).strip()

def obtener_monto_por_emoji(emoji):
    """Tus montos y emojis originales de negocio."""
    mapeo = {"💖": 3300.0, "⭐": 20.0, "💎": 10.0}
    return mapeo.get(emoji, 0.0)

def buscar_todas_las_respuestas(texto_usuario):
    """Busca en Supabase las respuestas automatizadas por palabras clave."""
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
        print(f"❌ Error BD en buscar_todas_las_respuestas: {e}")
    return lista_respuestas

def buscar_respuesta_unica(texto_usuario):
    """Busca una coincidencia directa o devuelve la primera disponible."""
    respuestas = buscar_todas_las_respuestas(texto_usuario)
    return respuestas[0] if respuestas else None

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
            # Si el error reporta alta demanda (503) y nos quedan intentos, esperamos y reintentamos
            if "503" in str(e) and intento < intentos_maximos - 1:
                print(f"⚠️ Servidor saturado (503). Reintentando en {espera}s... (Intento {intento + 1}/{intentos_maximos})")
                time.sleep(espera)
                espera *= 2  # Aumento exponencial del tiempo (2s, 4s...)
            else:
                print(f"❌ Error crítico final en verificar_pago_movil: {e}")
                return "❌ Error transitorio del sistema (Código 503). Por favor, intenta enviar tu capture nuevamente en unos instantes."

def verificar_capture_con_gemini(image_bytes: bytes, monto_esperado: float):
    """
    Función puente/alias para mantener compatibilidad con las llamadas 
    en segundo plano (background tasks) que pueda invocar tu web_server.py.
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
        res = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
        return res.data[0] if res.data else {"cedula_esperada": "0", "telefono_esperado": "0"}
    except Exception as e:
        print(f"❌ Error al obtener datos de verificación: {e}")
        return {"cedula_esperada": "0", "telefono_esperado": "0"}

def set_user_state(phone, state):
    """Registra o actualiza el estado de la conversación del cliente."""
    try:
        supabase.table("estados_usuario").upsert({"phone": phone, "estado": state}).execute()
    except Exception as e:
        print(f"❌ Error en set_user_state: {e}")

def get_user_state(phone):
    """Consulta el estado actual en el que se encuentra el cliente."""
    try:
        res = supabase.table("estados_usuario").select("estado").eq("phone", phone).execute()
        return res.data[0]['estado'] if res.data else "IDLE"
    except Exception as e:
        print(f"❌ Error en get_user_state: {e}")
        return "IDLE"

def save_to_db(phone, response, text=None, url_path=None):
    """Guarda el log del mensaje procesado en el historial."""
    try:
        data = {"phone": phone, "respuesta": response}
        if text: data["texto_usuario"] = text
        if url_path: data["url_imagen"] = url_path
        supabase.table("historial_mensajes").insert(data).execute()
    except Exception as e:
        print(f"❌ Error guardando historial: {e}")
