"""
Supabase Client — חיבור למסד הנתונים דרך REST API
מעוף Tech-Lead Israel

משתמש ב-httpx ישירות (ללא supabase library) — אמין יותר.
Fallback: in-memory אם אין env vars.
"""

import os
import httpx
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

_last_error = ""


def _headers() -> Dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def is_connected() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


def get_last_error() -> str:
    return _last_error


# ─── Generic REST operations ─────────────────────────────────

def _select(table: str, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
    global _last_error
    if not is_connected():
        _last_error = "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY"
        return []
    try:
        params = {"limit": limit}
        if filters:
            params.update(filters)
        r = httpx.get(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=_headers(),
            params=params,
            timeout=10.0
        )
        r.raise_for_status()
        _last_error = ""
        return r.json()
    except Exception as e:
        _last_error = str(e)
        return []


def _insert(table: str, data: Dict) -> Optional[Dict]:
    global _last_error
    if not is_connected():
        return None
    try:
        r = httpx.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=_headers(),
            json=data,
            timeout=10.0
        )
        r.raise_for_status()
        result = r.json()
        _last_error = ""
        return result[0] if isinstance(result, list) and result else data
    except Exception as e:
        _last_error = str(e)
        return None


def _upsert(table: str, data: Dict) -> Optional[Dict]:
    global _last_error
    if not is_connected():
        return None
    try:
        headers = {**_headers(), "Prefer": "resolution=merge-duplicates,return=representation"}
        r = httpx.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=headers,
            json=data,
            timeout=10.0
        )
        r.raise_for_status()
        result = r.json()
        _last_error = ""
        return result[0] if isinstance(result, list) and result else data
    except Exception as e:
        _last_error = str(e)
        return None


def _count(table: str) -> int:
    global _last_error
    if not is_connected():
        return 0
    try:
        headers = {**_headers(), "Prefer": "count=exact"}
        r = httpx.get(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=headers,
            params={"limit": 0},
            timeout=10.0
        )
        r.raise_for_status()
        content_range = r.headers.get("content-range", "0/0")
        total = content_range.split("/")[-1]
        return int(total) if total.isdigit() else 0
    except Exception as e:
        _last_error = str(e)
        return 0


def _delete(table: str, filters: Dict) -> bool:
    global _last_error
    if not is_connected():
        _last_error = "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY"
        return False
    try:
        r = httpx.delete(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=_headers(),
            params=filters,
            timeout=10.0
        )
        r.raise_for_status()
        _last_error = ""
        return True
    except Exception as e:
        _last_error = str(e)
        return False


# ─── Public API ──────────────────────────────────────────────

def db_upsert(table: str, data: Dict) -> Optional[Dict]:
    return _upsert(table, data)

def db_insert(table: str, data: Dict) -> Optional[Dict]:
    return _insert(table, data)

def db_select(table: str, filters: Optional[Dict] = None, limit: int = 100) -> List[Dict]:
    return _select(table, filters, limit)

def db_count(table: str) -> int:
    return _count(table)

def db_delete(table: str, filters: Dict) -> bool:
    return _delete(table, filters)
