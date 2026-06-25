import os
from supabase import create_client

def get_supabase():
    """
    Inicializa el cliente de Supabase sin argumentos adicionales para 
    evitar conflictos de versiones con ClientOptions.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("Las variables de entorno SUPABASE_URL y SUPABASE_KEY son necesarias.")
        
    return create_client(url, key)
