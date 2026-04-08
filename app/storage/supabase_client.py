import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL:
    raise RuntimeError(
        "Missing SUPABASE_URL in environment. "
        "Create a .env file in the project root and add SUPABASE_URL=..."
    )

if not SUPABASE_SERVICE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_SERVICE_KEY in environment. "
        "Create a .env file in the project root and add SUPABASE_SERVICE_KEY=..."
    )

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)