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
from scoring.score_a import calculate_score_a
from scoring.score_b import calculate_score_b
from scoring.score_c import calculate_score_c
from scoring.volume import calculate_volume_score
from matching.hungarian import run_hungarian
from data.synthetic import generate_dataset
from main import run_full_matching
from genetic.optimizer import run_genetic_optimizer
from nlp.eli5_analyzer import analyze_eli5
from feedback.loop import FeedbackLoop, PlacementRecord, SchoolFeedback, CompanyFeedback, CandidateFeedback

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
    return {"status": "ok", "engine": "Maof Dual Scoring Engine v1.0"}


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
    if not text:
        raise HTTPException(status_code=400, detail="חסר שדה 'text'")
    return analyze_eli5(text)


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
