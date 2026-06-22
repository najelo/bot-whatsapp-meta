import os
from supabase import create_client, ClientOptions

def get_supabase():
    # Aumentamos el timeout a 30 segundos para evitar errores 522 al iniciar
    options = ClientOptions(timeout=30) 
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"), options=options)
