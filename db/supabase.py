import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

def create_supabase_client() -> Client:
    supabase: Client = create_client(url, key)
    return supabase