"""
FastAPI Routes — מעוף Dual Scoring Engine
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from models.candidate import Candidate
from models.school import School
from models.company import Company
from scoring.score_a import calculate_score_a, calculate_score_a_detailed
from scoring.score_b import calculate_score_b, calculate_score_b_detailed
from scoring.score_c import calculate_score_c
from scoring.volume import calculate_volume_score
from matching.hungarian import run_hungarian
from data.synthetic import generate_dataset
from main import run_full_matching
from genetic.optimizer import run_genetic_optimizer
from nlp.eli5_analyzer import analyze_eli5
from nlp.llm_comparator import analyze_with_llm_comparison
from nlp.eli5_chatbot import run_adaptive_session, get_next_question
from nlp.groq_eli5 import analyze_eli5_full
from nlp.code_test import run_code_test, get_first_question
from nlp.systemic_test import get_opening_question, get_next_question as get_systemic_next, score_chain
from nlp.semantic_match import get_semantic_similarity
from feedback.loop import FeedbackLoop, PlacementRecord, SchoolFeedback, CompanyFeedback, CandidateFeedback
from database import repository as db
from database.client import is_connected, get_last_error

router = APIRouter()

# Global feedback loop instance
_feedback_loop = FeedbackLoop()


# --- Request / Response Models ---

class ScoreRequest(BaseModel):
    candidate: Candidate
    school: School
    company: Company
    total_placements: int = 0


class ScoreResponse(BaseModel):
    score_a: float
    score_b: float
    score_c: float
    volume_score: float
    final_score: float
    passes_threshold: bool
    breakdown: dict


class WhatIfRequest(BaseModel):
    candidate: Candidate
    school: School
    company: Company
    field: str
    new_value: float
    total_placements: int = 0


class RecommendRequest(BaseModel):
    candidate: Candidate
    schools: List[School]
    companies: List[Company]
    top_n: int = 3
    total_placements: int = 0


class MatchRequest(BaseModel):
    candidates: List[Candidate]
    schools: List[School]
    companies: List[Company]
    total_placements: int = 0


class SimulateRequest(BaseModel):
    n_candidates: int = 10
    n_schools: int = 5
    n_companies: int = 5


class OptimizeRequest(BaseModel):
    n_candidates: int = 10
    n_schools: int = 5
    n_companies: int = 5
    population_size: int = 20
    generations: int = 30


# --- Endpoints ---

@router.get("/health")
def health():
    connected = is_connected()
    return {
        "status": "ok",
        "engine": "Maof Dual Scoring Engine v1.0",
        "database": "supabase" if connected else "in-memory",
        "db_error": get_last_error() if not connected else None,
    }


# ─── Database CRUD Endpoints ────────────────────────────────

@router.post("/candidates")
def create_candidate(body: dict):
    """שמור מועמד חדש למסד הנתונים"""
    if "id" not in body:
        raise HTTPException(status_code=400, detail="חסר שדה 'id'")
    return db.upsert_candidate(body)


@router.get("/candidates")
def list_candidates(limit: int = 50):
    """רשימת כל המועמדים"""
    candidates = db.list_candidates(limit)
    return {"candidates": candidates, "count": len(candidates)}


@router.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: str):
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="מועמד לא נמצא")
    return candidate


@router.delete("/candidates/{candidate_id}")
def delete_candidate(candidate_id: str):
    """מחיקת מועמד"""
    if not db.delete_candidate(candidate_id):
        raise HTTPException(status_code=404, detail="מועמד לא נמצא")
    return {"status": "deleted", "id": candidate_id}


@router.post("/candidates/{candidate_id}/complete-assessment")
def complete_assessment(candidate_id: str, body: dict):
    """
    סגירת פייפליין הערכה — מקבל תוצאות מבחנים וסוגר את הציונים על המועמד.

    body:
      eli5_score     — ציון ELI5 (סבבים 1-3)   [0-100]
      code_score     — ציון מבחן קוד (סבב 4)   [0-100]  (אופציונלי)
      systemic_score — ציון חשיבה מערכתית       [0-100]  (אופציונלי)
      topic          — נושא המבחן               (אופציונלי)

    מחשב:
      tech_test_score = systemic_score × 0.55 + code_score × 0.45
      (fallback: אם חסר אחד, משתמש בקיים בלבד)

    מעדכן את המועמד ב-DB ומחזיר את הציונים המחושבים.
    """
    candidate = db.get_candidate(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="מועמד לא נמצא")

    eli5       = body.get("eli5_score")
    code       = body.get("code_score")
    systemic   = body.get("systemic_score")

    # --- וולידציה ---
    for name, val in [("eli5_score", eli5), ("code_score", code), ("systemic_score", systemic)]:
        if val is not None and not (0 <= float(val) <= 100):
            raise HTTPException(status_code=400, detail=f"'{name}' חייב להיות בין 0 ל-100")

    # --- חישוב tech_test_score ---
    c = float(code     or candidate.get("code_score",     0))
    s = float(systemic or candidate.get("systemic_score", 0))

    if s > 0 and c > 0:
        tech_test = round(s * 0.55 + c * 0.45, 2)
    elif s > 0:
        tech_test = round(s, 2)
    elif c > 0:
        tech_test = round(c, 2)
    else:
        tech_test = float(candidate.get("tech_test_score", 0))

    # --- עדכון ---
    updates = {"tech_test_score": tech_test}
    if eli5     is not None: updates["eli5_score"]     = round(float(eli5), 2)
    if code     is not None: updates["code_score"]     = round(float(code), 2)
    if systemic is not None: updates["systemic_score"] = round(float(systemic), 2)
    if body.get("topic"):    updates["subject"]        = body["topic"]

    candidate.update(updates)
    db.upsert_candidate(candidate)

    return {
        "status":          "updated",
        "candidate_id":    candidate_id,
        "eli5_score":      candidate.get("eli5_score"),
        "code_score":      candidate.get("code_score"),
        "systemic_score":  candidate.get("systemic_score"),
        "tech_test_score": tech_test,
        "pipeline_complete": all([
            candidate.get("eli5_score", 0) > 0,
            tech_test > 0,
        ]),
    }


@router.post("/schools")
def create_school(body: dict):
    """שמור בית ספר חדש"""
    if "id" not in body:
        raise HTTPException(status_code=400, detail="חסר שדה 'id'")
    return db.upsert_school(body)


@router.get("/schools")
def list_schools(limit: int = 50):
    schools = db.list_schools(limit)
    return {"schools": schools, "count": len(schools)}


@router.post("/companies")
def create_company(body: dict):
    """שמור חברה חדשה"""
    if "id" not in body:
        raise HTTPException(status_code=400, detail="חסר שדה 'id'")
    return db.upsert_company(body)


@router.get("/companies")
def list_companies(limit: int = 50):
    companies = db.list_companies(limit)
    return {"companies": companies, "count": len(companies)}


@router.get("/placements")
def list_placements(limit: int = 50):
    """רשימת כל השיבוצים — ממוין לפי ציון"""
    return {"placements": db.list_placements(limit)}


@router.get("/stats")
def global_stats():
    """סטטיסטיקות מסד הנתונים"""
    return db.get_global_stats()


@router.post("/eli5/save")
def save_eli5(body: dict):
    """שמור תוצאת ELI5 למסד הנתונים"""
    candidate_id = body.get("candidate_id", "")
    topic = body.get("topic", "")
    result = body.get("result", {})
    if not candidate_id:
        raise HTTPException(status_code=400, detail="חסר 'candidate_id'")
    return db.save_eli5_result(candidate_id, topic, result)


@router.get("/eli5/history/{candidate_id}")
def eli5_history(candidate_id: str):
    """היסטוריית מבחני ELI5 של מועמד"""
    return {"history": db.get_eli5_history(candidate_id)}


@router.post("/code/save")
def save_code_test(body: dict):
    """שמור תוצאת מבחן קוד"""
    candidate_id = body.get("candidate_id", "")
    result = body.get("result", {})
    if not candidate_id:
        raise HTTPException(status_code=400, detail="חסר 'candidate_id'")
    return db.save_code_test_result(candidate_id, result)


@router.post("/score", response_model=ScoreResponse)
def score_single(req: ScoreRequest):
    """ציון בודד — מועמד + בית ספר + חברה"""
    a = calculate_score_a(req.candidate, req.school)
    b = calculate_score_b(req.candidate, req.company)
    c = calculate_score_c(a, b, req.candidate, req.school, req.company, req.total_placements)
    vol = calculate_volume_score(a, b, c)

    return ScoreResponse(
        score_a=a,
        score_b=b,
        score_c=c,
        volume_score=vol["volume_score"],
        final_score=vol["final_score"],
        passes_threshold=vol["passes_threshold"],
        breakdown=vol["breakdown"],
    )


@router.post("/score/breakdown")
def score_breakdown(req: ScoreRequest):
    """פירוט מלא — כל תת-מדד עם הסבר"""
    detail_a = calculate_score_a_detailed(req.candidate, req.school)
    detail_b = calculate_score_b_detailed(req.candidate, req.company)
    a = detail_a["total"]
    b = detail_b["total"]
    c = calculate_score_c(a, b, req.candidate, req.school, req.company, req.total_placements)
    vol = calculate_volume_score(a, b, c)

    return {
        "score_a": detail_a,
        "score_b": detail_b,
        "score_c": c,
        "volume_score": vol["volume_score"],
        "final_score": vol["final_score"],
        "passes_threshold": vol["passes_threshold"],
        "summary": f"ציון סופי: {vol['final_score']} | A={a} B={b} C={c} | {'עובר סף' if vol['passes_threshold'] else 'לא עובר סף 60'}",
    }


@router.post("/score/whatif")
def score_whatif(req: WhatIfRequest):
    """What-If — שנה פרמטר אחד וראה before/after"""
    ALLOWED_FIELDS = {
        "eli5_score", "distance_km", "tech_test_score", "commitment_score",
        "family_status_score", "conflict_resolution_score", "promotion_rate",
        "willing_periphery", "willing_relocate", "career_switches",
        "independent_courses", "team_size",
    }
    if req.field not in ALLOWED_FIELDS:
        raise HTTPException(status_code=400, detail=f"שדה '{req.field}' לא נתמך. שדות: {', '.join(sorted(ALLOWED_FIELDS))}")

    a_before = calculate_score_a(req.candidate, req.school)
    b_before = calculate_score_b(req.candidate, req.company)
    c_before = calculate_score_c(a_before, b_before, req.candidate, req.school, req.company, req.total_placements)
    vol_before = calculate_volume_score(a_before, b_before, c_before)

    modified = req.candidate.model_copy(update={req.field: req.new_value})

    a_after = calculate_score_a(modified, req.school)
    b_after = calculate_score_b(modified, req.company)
    c_after = calculate_score_c(a_after, b_after, modified, req.school, req.company, req.total_placements)
    vol_after = calculate_volume_score(a_after, b_after, c_after)

    delta = round(vol_after["final_score"] - vol_before["final_score"], 2)
    direction = "עלייה" if delta > 0 else "ירידה" if delta < 0 else "ללא שינוי"

    return {
        "field": req.field,
        "old_value": getattr(req.candidate, req.field),
        "new_value": req.new_value,
        "before": {
            "score_a": a_before, "score_b": b_before, "score_c": c_before,
            "final_score": vol_before["final_score"], "passes_threshold": vol_before["passes_threshold"],
        },
        "after": {
            "score_a": a_after, "score_b": b_after, "score_c": c_after,
            "final_score": vol_after["final_score"], "passes_threshold": vol_after["passes_threshold"],
        },
        "delta": delta,
        "direction": direction,
        "explanation": f"שינוי {req.field} מ-{getattr(req.candidate, req.field)} ל-{req.new_value} → {direction} של {abs(delta)} נקודות (ציון סופי: {vol_before['final_score']} → {vol_after['final_score']})",
    }


@router.post("/recommend")
def recommend_placements(req: RecommendRequest):
    """Top-N שילובים מומלצים למועמד עם הסבר"""
    if not req.schools or not req.companies:
        raise HTTPException(status_code=400, detail="חסרים בתי ספר או חברות")

    results = []
    for school in req.schools:
        for company in req.companies:
            detail_a = calculate_score_a_detailed(req.candidate, school)
            detail_b = calculate_score_b_detailed(req.candidate, company)
            a = detail_a["total"]
            b = detail_b["total"]
            c = calculate_score_c(a, b, req.candidate, school, company, req.total_placements)
            vol = calculate_volume_score(a, b, c)

            results.append({
                "school_id": school.id,
                "school_name": school.name,
                "company_id": company.id,
                "company_name": company.name,
                "score_a": a,
                "score_b": b,
                "score_c": c,
                "final_score": vol["final_score"],
                "passes_threshold": vol["passes_threshold"],
                "explanation_a": detail_a["explanation"],
                "explanation_b": detail_b["explanation"],
                "strength_a": max(detail_a["components"].items(), key=lambda x: x[1]["raw"])[0],
                "strength_b": max(detail_b["components"].items(), key=lambda x: x[1]["raw"])[0],
            })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    top = results[:req.top_n]

    return {
        "candidate_id": req.candidate.id,
        "candidate_name": req.candidate.name,
        "total_combinations": len(results),
        "recommendations": top,
        "summary": f"מתוך {len(results)} שילובים, ה-{len(top)} הטובים: " + ", ".join(
            f"{r['school_name']}+{r['company_name']} ({r['final_score']})" for r in top
        ),
    }


@router.post("/match")
def match_all(req: MatchRequest):
    """שיבוץ גלובלי — Hungarian Algorithm על כל המועמדים"""
    if not req.candidates:
        raise HTTPException(status_code=400, detail="אין מועמדים")
    if not req.schools or not req.companies:
        raise HTTPException(status_code=400, detail="אין בתי ספר או חברות")

    results = run_full_matching(
        req.candidates,
        req.schools,
        req.companies,
        req.total_placements
    )
    return results


@router.post("/simulate")
def simulate(req: SimulateRequest):
    """סימולציה עם נתונים סינתטיים"""
    if req.n_candidates > 50:
        raise HTTPException(status_code=400, detail="מקסימום 50 מועמדים לסימולציה")

    candidates, schools, companies = generate_dataset(
        req.n_candidates,
        req.n_schools,
        req.n_companies
    )

    results = run_full_matching(candidates, schools, companies)
    return {
        "input": {
            "candidates": req.n_candidates,
            "schools": req.n_schools,
            "companies": req.n_companies,
        },
        "results": results
    }


@router.post("/optimize")
def optimize_weights(req: OptimizeRequest):
    """Genetic Algorithm — כיוון משקלות על נתונים סינתטיים"""
    if req.generations > 100:
        raise HTTPException(status_code=400, detail="מקסימום 100 דורות")

    candidates, schools, companies = generate_dataset(
        req.n_candidates, req.n_schools, req.n_companies
    )

    result = run_genetic_optimizer(
        candidates, schools, companies,
        population_size=req.population_size,
        generations=req.generations,
        verbose=False,
    )
    return result


@router.post("/eli5")
def score_eli5(body: dict):
    """ניתוח ELI5 — מנתח טקסט הסבר ומחזיר ציון"""
    text = body.get("text", "")
    topic = body.get("topic", "")
    if not text:
        raise HTTPException(status_code=400, detail="חסר שדה 'text'")
    return analyze_eli5(text, topic=topic)


@router.post("/eli5/compare")
def score_eli5_compare(body: dict):
    """ניתוח ELI5 + השוואה ל-LLM reference + בונוס תמציתיות"""
    text = body.get("text", "")
    topic = body.get("topic", "")
    if not text:
        raise HTTPException(status_code=400, detail="חסר שדה 'text'")
    if not topic:
        raise HTTPException(status_code=400, detail="חסר שדה 'topic'")
    return analyze_with_llm_comparison(text, topic)


@router.post("/eli5/groq")
def score_eli5_groq(body: dict):
    """ניתוח ELI5 + Groq LLM layer (analogy quality, conclusion logic, audience fit)"""
    text = body.get("text", "")
    topic = body.get("topic", "")
    if not text:
        raise HTTPException(status_code=400, detail="חסר שדה 'text'")
    return analyze_eli5_full(text, topic=topic)


@router.post("/eli5/chatbot")
def eli5_chatbot(body: dict):
    """מבחן ELI5 אדפטיבי — שאלות מתקדמות לפי ביצועים"""
    topic = body.get("topic", "")
    answers = body.get("answers", [])
    if not topic:
        raise HTTPException(status_code=400, detail="חסר שדה 'topic'")
    if not isinstance(answers, list):
        raise HTTPException(status_code=400, detail="'answers' חייב להיות רשימה")
    return run_adaptive_session(topic, answers)


@router.get("/eli5/chatbot/question")
def eli5_next_question(topic: str, level: int = 0):
    """מחזיר שאלה לפי נושא ורמה"""
    q = get_next_question(topic, level)
    if not q:
        raise HTTPException(status_code=404, detail="אין שאלה ברמה זו")
    return q


@router.post("/code/test")
def code_test(body: dict):
    """מבחן קוד אדפטיבי — שאלות טכניות מתקדמות"""
    answers = body.get("answers", [])
    tech_stack = body.get("tech_stack", [])
    if not isinstance(answers, list):
        raise HTTPException(status_code=400, detail="'answers' חייב להיות רשימה")
    return run_code_test(answers, tech_stack)


@router.get("/code/test/first")
def code_first_question(tech_stack: str = ""):
    """מחזיר שאלה ראשונה לפי Tech Stack"""
    stack = [t.strip() for t in tech_stack.split(",") if t.strip()] if tech_stack else []
    return get_first_question(stack)


# ══════════════════════════════════════════════
#  Systemic Thinking Test — Score B Component
# ══════════════════════════════════════════════

@router.get("/systemic/start")
def systemic_start(topic: str = ""):
    """שאלת פתיחה למבחן חשיבה מערכתית"""
    return get_opening_question(topic)


@router.post("/systemic/next")
def systemic_next(body: dict):
    """
    מחזיר שאלת המשך לפי היסטוריית השיחה.
    body: { "topic": str, "qa_pairs": [{"question": str, "answer": str}] }
    """
    topic    = body.get("topic", "")
    qa_pairs = body.get("qa_pairs", [])
    if not isinstance(qa_pairs, list):
        raise HTTPException(status_code=400, detail="'qa_pairs' חייב להיות רשימה")
    return get_systemic_next(topic, qa_pairs)


@router.post("/systemic/score")
def systemic_score(body: dict):
    """
    ציון סופי לשרשרת שאלות-תשובות.
    body: { "topic": str, "qa_pairs": [{"question": str, "answer": str}] }
    """
    topic    = body.get("topic", "")
    qa_pairs = body.get("qa_pairs", [])
    if not qa_pairs:
        raise HTTPException(status_code=400, detail="חסרות תשובות לניתוח")
    return score_chain(topic, qa_pairs)


@router.post("/semantic/match")
def semantic_match(body: dict):
    """השוואה סמנטית בין שתי רשימות מונחים"""
    terms_a = body.get("terms_a", [])
    terms_b = body.get("terms_b", [])
    if not terms_a or not terms_b:
        raise HTTPException(status_code=400, detail="חסרים שדות 'terms_a' ו-'terms_b'")
    return get_semantic_similarity(terms_a, terms_b)


@router.post("/feedback/placement")
def add_placement(body: dict):
    """רישום שיבוץ חדש ל-Feedback Loop"""
    try:
        record = PlacementRecord(
            placement_id=body["placement_id"],
            candidate_id=body["candidate_id"],
            school_id=body["school_id"],
            company_id=body["company_id"],
            predicted_score=body["predicted_score"],
        )
        _feedback_loop.add_placement(record)
        return {"status": "ok", "placement_id": record.placement_id}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"חסר שדה: {e}")


@router.post("/feedback/school")
def add_school_feedback(body: dict):
    """משוב בית ספר"""
    try:
        feedback = SchoolFeedback(
            placement_id=body["placement_id"],
            candidate_id=body["candidate_id"],
            school_id=body["school_id"],
            date=body.get("date", ""),
            teacher_rating=body["teacher_rating"],
            attendance_rate=body["attendance_rate"],
            principal_satisfaction=body["principal_satisfaction"],
            student_satisfaction=body["student_satisfaction"],
        )
        _feedback_loop.add_school_feedback(body["placement_id"], feedback)
        return {"status": "ok", "actual_score": feedback.actual_score}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/feedback/company")
def add_company_feedback(body: dict):
    """משוב חברת הייטק"""
    try:
        feedback = CompanyFeedback(
            placement_id=body["placement_id"],
            candidate_id=body["candidate_id"],
            company_id=body["company_id"],
            date=body.get("date", ""),
            performance_score=body["performance_score"],
            progression_rate=body["progression_rate"],
            manager_satisfaction=body["manager_satisfaction"],
        )
        _feedback_loop.add_company_feedback(body["placement_id"], feedback)
        return {"status": "ok", "actual_score": feedback.actual_score}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/feedback/candidate")
def add_candidate_feedback(body: dict):
    """משוב מועמד"""
    try:
        feedback = CandidateFeedback(
            placement_id=body["placement_id"],
            candidate_id=body["candidate_id"],
            date=body.get("date", ""),
            school_satisfaction=body["school_satisfaction"],
            company_satisfaction=body["company_satisfaction"],
            overall_satisfaction=body["overall_satisfaction"],
        )
        _feedback_loop.add_candidate_feedback(body["placement_id"], feedback)
        return {"status": "ok", "actual_score": feedback.actual_score}
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/feedback/placement/{placement_id}")
def get_placement_feedback(placement_id: str):
    """כל המשוב לשיבוץ ספציפי"""
    from database import repository as db
    feedback = db.get_feedback_for_placement(placement_id)
    return feedback


@router.get("/feedback/stats")
def get_feedback_stats():
    """סטטיסטיקות Feedback Loop"""
    return {
        "stats": _feedback_loop.get_stats(),
        "errors": _feedback_loop.analyze_errors(),
        "suggestion": _feedback_loop.suggest_weight_update(),
    }


@router.get("/feedback/export")
def export_feedback():
    """ייצוא נתונים לאימון מחדש"""
    data = _feedback_loop.export_for_retraining()
    return {"count": len(data), "data": data}


@router.get("/simulate/quick")
def simulate_quick():
    """סימולציה מהירה — 5 מועמדים, 3 בתי ספר, 3 חברות"""
    candidates, schools, companies = generate_dataset(5, 3, 3)
    return run_full_matching(candidates, schools, companies)
