import os
from supabase import create_client, ClientOptions

def get_supabase():
    options = ClientOptions(timeout=30) 
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"), options=options)
