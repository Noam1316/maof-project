"""
Repository — שכבת גישה לנתונים
מעוף Tech-Lead Israel

CRUD operations לכל הטבלאות.
אם אין Supabase → in-memory fallback.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import List, Optional, Dict
from database.client import is_connected, db_upsert, db_insert, db_select, db_count, db_delete

# ─── In-Memory Fallback ──────────────────────────────────────
_memory: Dict = {
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


# ─── Candidates ─────────────────────────────────────────────

def upsert_candidate(data: Dict) -> Dict:
    if is_connected():
        result = db_upsert("candidates", data)
        return result or data
    _memory["candidates"][data["id"]] = data
    return data


def get_candidate(candidate_id: str) -> Optional[Dict]:
    if is_connected():
        rows = db_select("candidates", {"id": f"eq.{candidate_id}"}, limit=1)
        return rows[0] if rows else None
    return _memory["candidates"].get(candidate_id)


def list_candidates(limit: int = 100) -> List[Dict]:
    if is_connected():
        return db_select("candidates", limit=limit)
    return list(_memory["candidates"].values())[:limit]


def delete_candidate(candidate_id: str) -> bool:
    if is_connected():
        return db_delete("candidates", {"id": f"eq.{candidate_id}"})
    if candidate_id in _memory["candidates"]:
        del _memory["candidates"][candidate_id]
        return True
    return False


# ─── Schools ────────────────────────────────────────────────

def upsert_school(data: Dict) -> Dict:
    if is_connected():
        result = db_upsert("schools", data)
        return result or data
    _memory["schools"][data["id"]] = data
    return data


def get_school(school_id: str) -> Optional[Dict]:
    if is_connected():
        rows = db_select("schools", {"id": f"eq.{school_id}"}, limit=1)
        return rows[0] if rows else None
    return _memory["schools"].get(school_id)


def list_schools(limit: int = 100) -> List[Dict]:
    if is_connected():
        return db_select("schools", limit=limit)
    return list(_memory["schools"].values())[:limit]


# ─── Companies ──────────────────────────────────────────────

def upsert_company(data: Dict) -> Dict:
    if is_connected():
        result = db_upsert("companies", data)
        return result or data
    _memory["companies"][data["id"]] = data
    return data


def get_company(company_id: str) -> Optional[Dict]:
    if is_connected():
        rows = db_select("companies", {"id": f"eq.{company_id}"}, limit=1)
        return rows[0] if rows else None
    return _memory["companies"].get(company_id)


def list_companies(limit: int = 100) -> List[Dict]:
    if is_connected():
        return db_select("companies", limit=limit)
    return list(_memory["companies"].values())[:limit]


# ─── Placements ─────────────────────────────────────────────

def save_placement(data: Dict) -> Dict:
    if is_connected():
        result = db_upsert("placements", data)
        return result or data
    _memory["placements"][data["id"]] = data
    return data


def get_placement(placement_id: str) -> Optional[Dict]:
    if is_connected():
        rows = db_select("placements", {"id": f"eq.{placement_id}"}, limit=1)
        return rows[0] if rows else None
    return _memory["placements"].get(placement_id)


def list_placements(limit: int = 100) -> List[Dict]:
    if is_connected():
        return db_select("placements", limit=limit)
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
    if is_connected():
        return db_insert("eli5_results", record) or record
    _memory["eli5_results"].append(record)
    return record


def get_eli5_history(candidate_id: str) -> List[Dict]:
    if is_connected():
        return db_select("eli5_results", {"candidate_id": f"eq.{candidate_id}"})
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
    if is_connected():
        return db_insert("code_test_results", record) or record
    _memory["code_test_results"].append(record)
    return record


# ─── Feedback ───────────────────────────────────────────────

def save_school_feedback(data: Dict) -> Dict:
    if is_connected():
        return db_insert("school_feedback", data) or data
    _memory["school_feedback"].append(data)
    return data


def save_company_feedback(data: Dict) -> Dict:
    if is_connected():
        return db_insert("company_feedback", data) or data
    _memory["company_feedback"].append(data)
    return data


def save_candidate_feedback(data: Dict) -> Dict:
    if is_connected():
        return db_insert("candidate_feedback", data) or data
    _memory["candidate_feedback"].append(data)
    return data


def get_feedback_for_placement(placement_id: str) -> Dict:
    if is_connected():
        school = db_select("school_feedback", {"placement_id": f"eq.{placement_id}"}, limit=1)
        company = db_select("company_feedback", {"placement_id": f"eq.{placement_id}"}, limit=1)
        candidate = db_select("candidate_feedback", {"placement_id": f"eq.{placement_id}"}, limit=1)
    else:
        school = [r for r in _memory["school_feedback"] if r.get("placement_id") == placement_id][:1]
        company = [r for r in _memory["company_feedback"] if r.get("placement_id") == placement_id][:1]
        candidate = [r for r in _memory["candidate_feedback"] if r.get("placement_id") == placement_id][:1]
    return {
        "school": school[0] if school else None,
        "company": company[0] if company else None,
        "candidate": candidate[0] if candidate else None,
    }


def list_all_placements_with_feedback(limit: int = 200) -> List[Dict]:
    placements = list_placements(limit)
    if not placements:
        return placements

    if is_connected():
        all_school_fb = db_select("school_feedback", limit=1000)
        all_company_fb = db_select("company_feedback", limit=1000)
        all_candidate_fb = db_select("candidate_feedback", limit=1000)
    else:
        all_school_fb = _memory["school_feedback"]
        all_company_fb = _memory["company_feedback"]
        all_candidate_fb = _memory["candidate_feedback"]

    school_by_pid = {}
    for fb in all_school_fb:
        school_by_pid.setdefault(fb.get("placement_id"), fb)
    company_by_pid = {}
    for fb in all_company_fb:
        company_by_pid.setdefault(fb.get("placement_id"), fb)
    candidate_by_pid = {}
    for fb in all_candidate_fb:
        candidate_by_pid.setdefault(fb.get("placement_id"), fb)

    for p in placements:
        pid = p.get("id", "")
        p["school_feedback"] = school_by_pid.get(pid)
        p["company_feedback"] = company_by_pid.get(pid)
        p["candidate_feedback"] = candidate_by_pid.get(pid)
    return placements


# ─── Stats ──────────────────────────────────────────────────

def get_global_stats() -> Dict:
    if is_connected():
        return {
            "candidates": db_count("candidates"),
            "schools": db_count("schools"),
            "companies": db_count("companies"),
            "placements": db_count("placements"),
            "storage": "supabase",
        }
    return {
        "candidates": len(_memory["candidates"]),
        "schools": len(_memory["schools"]),
        "companies": len(_memory["companies"]),
        "placements": len(_memory["placements"]),
        "storage": "in-memory",
    }
