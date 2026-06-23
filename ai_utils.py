# Añade esto al final de tu archivo ai_utils.py existente

def set_user_state(phone, state):
    """Guarda el estado del usuario: 'ESPERANDO_CAPTURE' o 'IDLE'."""
    try:
        supabase.table("estados_usuario").upsert({
            "phone": phone, 
            "estado": state
        }).execute()
    except Exception as e:
        print(f"Error guardando estado: {e}")

def get_user_state(phone):
    """Obtiene el estado actual del usuario."""
    try:
        res = supabase.table("estados_usuario").select("estado").eq("phone", phone).execute()
        return res.data[0]['estado'] if res.data else "IDLE"
    except:
        return "IDLE"
