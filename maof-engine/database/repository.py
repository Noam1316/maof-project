"""
Repository — שכבת גישה לנתונים
מעוף Tech-Lead Israel

CRUD operations לכל הטבלאות.
אם אין Supabase → in-memory fallback.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import List, Optional, Dict, Any
from datetime import date
from database.client import get_client

# ─── In-Memory Fallback ──────────────────────────────────────
_memory = {
    "candidates": {},
    "schools": {},
    "companies": {},
    "placements": {},
    "school_feedback": [],
    "company_feedback": [],
    "candidate_feedback": [],
    "eli5_results": [],
    "code_test_results": [],
}


def _use_db():
    return get_client() is not None


# ─── Candidates ─────────────────────────────────────────────

def upsert_candidate(data: Dict) -> Dict:
    """שמור או עדכן מועמד"""
    if _use_db():
        result = get_client().table("candidates").upsert(data).execute()
        return result.data[0] if result.data else data
    else:
        _memory["candidates"][data["id"]] = data
        return data


def get_candidate(candidate_id: str) -> Optional[Dict]:
    if _use_db():
        result = get_client().table("candidates").select("*").eq("id", candidate_id).execute()
        return result.data[0] if result.data else None
    return _memory["candidates"].get(candidate_id)


def list_candidates(limit: int = 100) -> List[Dict]:
    if _use_db():
        result = get_client().table("candidates").select("*").limit(limit).execute()
        return result.data or []
    return list(_memory["candidates"].values())[:limit]


def delete_candidate(candidate_id: str) -> bool:
    if _use_db():
        get_client().table("candidates").delete().eq("id", candidate_id).execute()
        return True
    if candidate_id in _memory["candidates"]:
        del _memory["candidates"][candidate_id]
        return True
    return False


# ─── Schools ────────────────────────────────────────────────

def upsert_school(data: Dict) -> Dict:
    if _use_db():
        result = get_client().table("schools").upsert(data).execute()
        return result.data[0] if result.data else data
    _memory["schools"][data["id"]] = data
    return data


def get_school(school_id: str) -> Optional[Dict]:
    if _use_db():
        result = get_client().table("schools").select("*").eq("id", school_id).execute()
        return result.data[0] if result.data else None
    return _memory["schools"].get(school_id)


def list_schools(limit: int = 100) -> List[Dict]:
    if _use_db():
        result = get_client().table("schools").select("*").limit(limit).execute()
        return result.data or []
    return list(_memory["schools"].values())[:limit]


# ─── Companies ──────────────────────────────────────────────

def upsert_company(data: Dict) -> Dict:
    if _use_db():
        result = get_client().table("companies").upsert(data).execute()
        return result.data[0] if result.data else data
    _memory["companies"][data["id"]] = data
    return data


def get_company(company_id: str) -> Optional[Dict]:
    if _use_db():
        result = get_client().table("companies").select("*").eq("id", company_id).execute()
        return result.data[0] if result.data else None
    return _memory["companies"].get(company_id)


def list_companies(limit: int = 100) -> List[Dict]:
    if _use_db():
        result = get_client().table("companies").select("*").limit(limit).execute()
        return result.data or []
    return list(_memory["companies"].values())[:limit]


# ─── Placements ─────────────────────────────────────────────

def save_placement(data: Dict) -> Dict:
    if _use_db():
        result = get_client().table("placements").upsert(data).execute()
        return result.data[0] if result.data else data
    _memory["placements"][data["id"]] = data
    return data


def get_placement(placement_id: str) -> Optional[Dict]:
    if _use_db():
        result = get_client().table("placements").select("*").eq("id", placement_id).execute()
        return result.data[0] if result.data else None
    return _memory["placements"].get(placement_id)


def list_placements(limit: int = 100) -> List[Dict]:
    if _use_db():
        result = (
            get_client().table("placements")
            .select("*, candidates(name), schools(name), companies(name)")
            .order("final_score", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    return sorted(
        _memory["placements"].values(),
        key=lambda x: x.get("final_score", 0),
        reverse=True
    )[:limit]


# ─── ELI5 Results ───────────────────────────────────────────

def save_eli5_result(candidate_id: str, topic: str, result: Dict) -> Dict:
    record = {
        "candidate_id": candidate_id,
        "topic": topic,
        "text_score": result.get("total_score", 0),
        "chatbot_score": result.get("chatbot_score"),
        "final_score": result.get("final_score", result.get("total_score", 0)),
        "passes_minimum": result.get("passes_minimum", False),
        "breakdown": result.get("breakdown", {}),
    }
    if _use_db():
        res = get_client().table("eli5_results").insert(record).execute()
        return res.data[0] if res.data else record
    _memory["eli5_results"].append(record)
    return record


def get_eli5_history(candidate_id: str) -> List[Dict]:
    if _use_db():
        result = (
            get_client().table("eli5_results")
            .select("*")
            .eq("candidate_id", candidate_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data or []
    return [r for r in _memory["eli5_results"] if r.get("candidate_id") == candidate_id]


# ─── Code Test Results ──────────────────────────────────────

def save_code_test_result(candidate_id: str, result: Dict) -> Dict:
    record = {
        "candidate_id": candidate_id,
        "domain": result.get("domain"),
        "final_level": result.get("final_level", 0),
        "adaptive_score": result.get("adaptive_score", 0),
        "passed": result.get("passed", False),
        "results": result.get("results", []),
    }
    if _use_db():
        res = get_client().table("code_test_results").insert(record).execute()
        return res.data[0] if res.data else record
    _memory["code_test_results"].append(record)
    return record


# ─── School Feedback ────────────────────────────────────────

def save_school_feedback(data: Dict) -> Dict:
    if _use_db():
        result = get_client().table("school_feedback").insert(data).execute()
        return result.data[0] if result.data else data
    _memory["school_feedback"].append(data)
    return data


# ─── Company Feedback ───────────────────────────────────────

def save_company_feedback(data: Dict) -> Dict:
    if _use_db():
        result = get_client().table("company_feedback").insert(data).execute()
        return result.data[0] if result.data else data
    _memory["company_feedback"].append(data)
    return data


# ─── Stats ──────────────────────────────────────────────────

def get_global_stats() -> Dict:
    if _use_db():
        db = get_client()
        candidates = db.table("candidates").select("id", count="exact").execute()
        schools = db.table("schools").select("id", count="exact").execute()
        companies = db.table("companies").select("id", count="exact").execute()
        placements = db.table("placements").select("id", count="exact").execute()
        return {
            "candidates": candidates.count or 0,
            "schools": schools.count or 0,
            "companies": companies.count or 0,
            "placements": placements.count or 0,
            "storage": "supabase",
        }
    return {
        "candidates": len(_memory["candidates"]),
        "schools": len(_memory["schools"]),
        "companies": len(_memory["companies"]),
        "placements": len(_memory["placements"]),
        "storage": "in-memory",
    }
