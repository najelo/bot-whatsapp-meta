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
    if not texto: return ""
    texto = unicodedata.normalize('NFD', texto.lower()).encode('ascii', 'ignore').decode('utf-8')
    return re.sub(r'[^a-z0-9\s]', '', texto).strip()

def obtener_monto_por_emoji(emoji):
    mapeo = {"💖": 3300.0, "⭐": 20.0, "💎": 10.0}
    return mapeo.get(emoji, 0.0)

def buscar_respuestas_en_cadena(texto_usuario):
    """
    Busca todas las respuestas configuradas en la BD para la palabra clave detectada,
    manteniendo el orden secuencial (Paso 1, Paso 2, etc.) e incluyendo su tipo.
    """
    texto_limpio = normalizar_texto(texto_usuario)
    lista_respuestas = []
    try:
        # 1. Traemos las palabras clave relacionadas con sus respuestas y tipos
        reglas = supabase.table("clientes").select(
            "id, palabra_clave, respuesta_id, respuestas(id, contenido, tipo_contenido)"
        ).execute().data
        
        # 2. Filtramos aquellas palabras clave que estén contenidas en el mensaje del usuario
        for r in reglas:
            pk_normalizada = normalizar_texto(r.get('palabra_clave', ''))
            if pk_normalizada and pk_normalizada in texto_limpio:
                resp_data = r.get('respuestas')
                if resp_data:
                    lista_respuestas.append({
                        "id_cliente_regla": r['id'], # Usamos el ID de la regla para mantener el orden de inserción
                        "contenido": resp_data.get("contenido"),
                        "tipo": resp_data.get("tipo_contenido", "texto")
                    })
                    
        # Ordenamos los mensajes por el ID de la regla para garantizar que salgan en secuencia correcta
        lista_respuestas.sort(key=lambda x: x["id_cliente_regla"])
        
    except Exception as e: 
        print(f"Error BD en buscar_respuestas_en_cadena: {e}")
        
    return lista_respuestas

def generar_respuesta_ia(texto_usuario):
    """Genera una respuesta utilizando la IA de Gemini si no hay regla en la BD."""
    try:
        prompt = f"Eres un asistente automatizado de atención al cliente. Responde de forma amable y concisa: {texto_usuario}"
        return model.generate_content(prompt).text
    except Exception as e:
        return f"Lo siento, presenté un inconveniente interno. Inténtalo de nuevo más tarde."

def verificar_pago_movil(img_bytes, cedula, telefono, monto_minimo):
    try:
        img = PIL.Image.open(io.BytesIO(img_bytes))
        prompt = (f"Auditor de pagos. Datos esperados: Cédula {cedula}, Teléfono {telefono}. "
                  f"Monto mínimo exigido: {monto_minimo}. Analiza el capture: "
                  "¿Coinciden los datos y el monto es igual o mayor al mínimo? "
                  "Responde: ✅ PAGO VERIFICADO o ❌ PAGO RECHAZADO.")
        return model.generate_content([prompt, img]).text
    except Exception as e: return f"Error IA: {e}"

def obtener_datos_verificacion():
    res = supabase.table("configuracion_pago").select("*").eq("activo", True).execute()
    return res.data[0] if res.data else {"cedula_esperada": "0", "telefono_esperado": "0"}

def set_user_state(phone, state):
    supabase.table("estados_usuario").upsert({"phone": phone, "estado": state}).execute()

def get_user_state(phone):
    res = supabase.table("estados_usuario").select("estado").eq("phone", phone).execute()
    return res.data[0]['estado'] if res.data else "IDLE"

def save_to_db(phone, response, text=None, url_path=None):
    try:
        data = {"phone": phone, "respuesta": response}
        if text: data["texto_usuario"] = text
        if url_path: data["url_imagen"] = url_path
        supabase.table("historial_mensajes").insert(data).execute()
    except: pass
