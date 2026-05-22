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


_last_error = ""

def get_client():
    """מחזיר Supabase client — singleton"""
    global _client, _last_error

    if _client is not None:
        return _client

    if not SUPABASE_URL or not SUPABASE_KEY:
        _last_error = f"Missing env vars: URL={'set' if SUPABASE_URL else 'missing'}, KEY={'set' if SUPABASE_KEY else 'missing'}"
        return None

    try:
        from supabase import create_client
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        _last_error = ""
        return _client
    except ImportError as e:
        _last_error = f"ImportError: {e}"
        return None
    except Exception as e:
        _last_error = f"Error: {e}"
        return None


def get_last_error() -> str:
    return _last_error


def is_connected() -> bool:
    """בודק אם יש חיבור ל-Supabase"""
    return get_client() is not None
