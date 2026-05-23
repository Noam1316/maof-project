"""
Feedback Loop — למידה מביצועים אמיתיים (persistent via Supabase)
מעוף Tech-Lead Israel

תדירות איסוף:
  בית ספר   → כל 3 חודשים (דירוג מורה, נוכחות, שביעות רצון)
  חברה       → כל 6 חודשים (ביצועים, קצב התקדמות)
  מועמד      → כל 6 חודשים (שביעות רצון)

השוואת ציון חיזוי vs ביצועים בפועל → עדכון משקלות אוטומטי.
כל הנתונים נשמרים ב-Supabase (או in-memory fallback).
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dataclasses import dataclass
from typing import List, Optional, Dict


# --- מבני נתונים ---

def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


@dataclass
class SchoolFeedback:
    placement_id: str
    candidate_id: str
    school_id: str
    date: str

    teacher_rating: float
    attendance_rate: float
    principal_satisfaction: float
    student_satisfaction: float

    def __post_init__(self):
        self.teacher_rating = _clamp(self.teacher_rating)
        self.attendance_rate = _clamp(self.attendance_rate)
        self.principal_satisfaction = _clamp(self.principal_satisfaction)
        self.student_satisfaction = _clamp(self.student_satisfaction)

    @property
    def actual_score(self) -> float:
        return round(
            self.teacher_rating * 0.40 +
            self.attendance_rate * 0.20 +
            self.principal_satisfaction * 0.25 +
            self.student_satisfaction * 0.15
        , 2)

    def to_dict(self) -> Dict:
        return {
            "placement_id": self.placement_id,
            "candidate_id": self.candidate_id,
            "school_id": self.school_id,
            "feedback_date": self.date or None,
            "teacher_rating": self.teacher_rating,
            "attendance_rate": self.attendance_rate,
            "principal_satisfaction": self.principal_satisfaction,
            "student_satisfaction": self.student_satisfaction,
            "actual_score": self.actual_score,
        }


@dataclass
class CompanyFeedback:
    placement_id: str
    candidate_id: str
    company_id: str
    date: str

    performance_score: float
    progression_rate: float
    manager_satisfaction: float

    def __post_init__(self):
        self.performance_score = _clamp(self.performance_score)
        self.progression_rate = _clamp(self.progression_rate)
        self.manager_satisfaction = _clamp(self.manager_satisfaction)

    @property
    def actual_score(self) -> float:
        return round(
            self.performance_score * 0.50 +
            self.progression_rate * 0.30 +
            self.manager_satisfaction * 0.20
        , 2)

    def to_dict(self) -> Dict:
        return {
            "placement_id": self.placement_id,
            "candidate_id": self.candidate_id,
            "company_id": self.company_id,
            "feedback_date": self.date or None,
            "performance_score": self.performance_score,
            "progression_rate": self.progression_rate,
            "manager_satisfaction": self.manager_satisfaction,
            "actual_score": self.actual_score,
        }


@dataclass
class CandidateFeedback:
    placement_id: str
    candidate_id: str
    date: str

    school_satisfaction: float
    company_satisfaction: float
    overall_satisfaction: float

    def __post_init__(self):
        self.school_satisfaction = _clamp(self.school_satisfaction)
        self.company_satisfaction = _clamp(self.company_satisfaction)
        self.overall_satisfaction = _clamp(self.overall_satisfaction)

    @property
    def actual_score(self) -> float:
        return round(
            self.school_satisfaction * 0.35 +
            self.company_satisfaction * 0.40 +
            self.overall_satisfaction * 0.25
        , 2)

    def to_dict(self) -> Dict:
        return {
            "placement_id": self.placement_id,
            "candidate_id": self.candidate_id,
            "feedback_date": self.date or None,
            "school_satisfaction": self.school_satisfaction,
            "company_satisfaction": self.company_satisfaction,
            "overall_satisfaction": self.overall_satisfaction,
            "actual_score": self.actual_score,
        }


@dataclass
class PlacementRecord:
    placement_id: str
    candidate_id: str
    school_id: str
    company_id: str
    predicted_score: float

    school_feedback: Optional[SchoolFeedback] = None
    company_feedback: Optional[CompanyFeedback] = None
    candidate_feedback: Optional[CandidateFeedback] = None

    @property
    def actual_score(self) -> Optional[float]:
        scores = []
        if self.school_feedback:
            scores.append(self.school_feedback.actual_score)
        if self.company_feedback:
            scores.append(self.company_feedback.actual_score)
        if self.candidate_feedback:
            scores.append(self.candidate_feedback.actual_score)
        return round(sum(scores) / len(scores), 2) if scores else None

    @property
    def prediction_error(self) -> Optional[float]:
        actual = self.actual_score
        if actual is None:
            return None
        return round(self.predicted_score - actual, 2)

    @property
    def has_full_feedback(self) -> bool:
        return (
            self.school_feedback is not None and
            self.company_feedback is not None and
            self.candidate_feedback is not None
        )


def _compute_actual_score(school_fb: Optional[Dict], company_fb: Optional[Dict], candidate_fb: Optional[Dict]) -> Optional[float]:
    scores = []
    if school_fb:
        scores.append(school_fb.get("actual_score", 0))
    if company_fb:
        scores.append(company_fb.get("actual_score", 0))
    if candidate_fb:
        scores.append(candidate_fb.get("actual_score", 0))
    return round(sum(scores) / len(scores), 2) if scores else None


# --- מנהל ה-Feedback Loop (Persistent) ---

class FeedbackLoop:
    """
    Feedback Loop with Supabase persistence.
    Saves all placements and feedback to DB, loads on demand.
    """

    def __init__(self):
        from database import repository as db
        self._db = db

    def add_placement(self, record: PlacementRecord) -> Dict:
        data = {
            "id": record.placement_id,
            "candidate_id": record.candidate_id,
            "school_id": record.school_id,
            "company_id": record.company_id,
            "predicted_score": record.predicted_score,
        }
        return self._db.save_placement(data)

    def add_school_feedback(self, placement_id: str, feedback: SchoolFeedback) -> Dict:
        placement = self._db.get_placement(placement_id)
        if not placement:
            raise ValueError(f"Placement {placement_id} not found")
        return self._db.save_school_feedback(feedback.to_dict())

    def add_company_feedback(self, placement_id: str, feedback: CompanyFeedback) -> Dict:
        placement = self._db.get_placement(placement_id)
        if not placement:
            raise ValueError(f"Placement {placement_id} not found")
        return self._db.save_company_feedback(feedback.to_dict())

    def add_candidate_feedback(self, placement_id: str, feedback: CandidateFeedback) -> Dict:
        placement = self._db.get_placement(placement_id)
        if not placement:
            raise ValueError(f"Placement {placement_id} not found")
        return self._db.save_candidate_feedback(feedback.to_dict())

    def _load_records(self) -> List[Dict]:
        return self._db.list_all_placements_with_feedback(limit=500)

    def get_stats(self) -> Dict:
        records = self._load_records()
        total = len(records)

        with_feedback = 0
        full_feedback = 0
        errors = []

        for r in records:
            sfb = r.get("school_feedback")
            cfb = r.get("company_feedback")
            canfb = r.get("candidate_feedback")
            actual = _compute_actual_score(sfb, cfb, canfb)

            if actual is not None:
                with_feedback += 1
                predicted = r.get("predicted_score", 0)
                if predicted:
                    errors.append(abs(predicted - actual))

            if sfb and cfb and canfb:
                full_feedback += 1

        mae = round(sum(errors) / len(errors), 2) if errors else None

        return {
            "total_placements": total,
            "with_some_feedback": with_feedback,
            "with_full_feedback": full_feedback,
            "mean_absolute_error": mae,
            "phase": self._get_phase(total),
            "storage": "supabase" if self._db.is_connected() else "in-memory",
        }

    def _get_phase(self, n: int) -> str:
        if n < 50:
            return "synthetic"
        elif n < 200:
            return "mixed"
        else:
            return "real_data"

    def analyze_errors(self) -> Dict:
        records = self._load_records()

        analyzed = []
        for r in records:
            sfb = r.get("school_feedback")
            cfb = r.get("company_feedback")
            canfb = r.get("candidate_feedback")
            actual = _compute_actual_score(sfb, cfb, canfb)
            predicted = r.get("predicted_score")
            if actual is not None and predicted:
                error = round(predicted - actual, 2)
                analyzed.append({
                    "placement_id": r.get("id"),
                    "predicted": predicted,
                    "actual": actual,
                    "error": error,
                })

        if not analyzed:
            return {"message": "אין מספיק נתונים לניתוח"}

        errors = [a["error"] for a in analyzed]
        avg_error = sum(errors) / len(errors)

        bias = "מנפחים ציונים" if avg_error > 5 else \
               "מזלזלים בציונים" if avg_error < -5 else \
               "ניבוי מאוזן"

        large_errors = [a for a in analyzed if abs(a["error"]) > 15]

        return {
            "n_analyzed": len(analyzed),
            "avg_error": round(avg_error, 2),
            "bias": bias,
            "large_errors": large_errors,
            "recommendation": self._get_recommendation(avg_error),
        }

    def _get_recommendation(self, avg_error: float) -> str:
        if avg_error > 10:
            return "הורד את המשקל של ציון A — אנחנו מנפחים יכולת הוראה"
        elif avg_error < -10:
            return "העלה את המשקל של ציון B — אנחנו מזלזלים בצד הטכני"
        elif -5 <= avg_error <= 5:
            return "המשקלות מאוזנות — המשך לאסוף נתונים"
        else:
            return "שקול להריץ Genetic Algorithm מחדש עם נתונים אמיתיים"

    def suggest_weight_update(self) -> Dict:
        analysis = self.analyze_errors()

        if "message" in analysis:
            return {"message": analysis["message"]}

        avg_error = analysis["avg_error"]
        learning_rate = 0.02

        delta_a = -learning_rate * avg_error / 100
        delta_b = learning_rate * avg_error / 100

        return {
            "current_analysis": analysis,
            "suggested_adjustments": {
                "score_a_weight_in_final": round(0.25 + delta_a, 3),
                "score_b_weight_in_final": round(0.25 + delta_b, 3),
                "volume_weight_in_final": 0.50,
            },
            "note": "הרץ Genetic Algorithm מחדש עם הנתונים האמיתיים לאחר 50+ שיבוצים"
        }

    def export_for_retraining(self) -> List[Dict]:
        records = self._load_records()
        result = []
        for r in records:
            sfb = r.get("school_feedback")
            cfb = r.get("company_feedback")
            canfb = r.get("candidate_feedback")
            actual = _compute_actual_score(sfb, cfb, canfb)
            predicted = r.get("predicted_score")
            if actual is not None:
                result.append({
                    "placement_id": r.get("id"),
                    "predicted_score": predicted,
                    "actual_score": actual,
                    "error": round(predicted - actual, 2) if predicted else None,
                    "has_full_feedback": sfb is not None and cfb is not None and canfb is not None,
                })
        return result
