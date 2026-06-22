import os
import io
import PIL.Image
import google.generativeai as genai
from supabase import create_client

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-3.5-flash')
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def process_text(text):
    return model.generate_content(text).text

def process_image(img_bytes):
    img = PIL.Image.open(io.BytesIO(img_bytes))
    return model.generate_content(["Describe esta imagen:", img]).text

def save_to_db(phone, response, text=None, url_path=None):
    supabase.table("mensajes").insert({
        "phone": phone, "texto": text, "url_archivo": url_path, "respuesta": response
    }).execute()
