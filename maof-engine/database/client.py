"""
Supabase Client — חיבור למסד הנתונים
מעוף Tech-Lead Israel

משתמש ב-SUPABASE_URL ו-SUPABASE_SERVICE_KEY מ-.env
Fallback: in-memory (לפיתוח מקומי ללא Supabase)
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

_client = None


def get_client():
    """מחזיר Supabase client — singleton"""
    global _client

    if _client is not None:
        return _client

    if not SUPABASE_URL or not SUPABASE_KEY:
        return None  # fallback mode

    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _client
    except ImportError:
        return None
    except Exception:
        return None


def is_connected() -> bool:
    """בודק אם יש חיבור ל-Supabase"""
    return get_client() is not None
