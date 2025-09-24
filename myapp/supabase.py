import os
from supabase import create_client, Client


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials are missing in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
