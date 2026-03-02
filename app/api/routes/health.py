from fastapi import APIRouter
from app.storage.supabase_client import supabase

router = APIRouter()

@router.get("/supabase")
def supabase_health():
    res = supabase.table("jobs").select("*").limit(1).execute()
    return {"supabase": "connected", "rows": len(res.data)}
