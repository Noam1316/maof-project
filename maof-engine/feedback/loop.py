"""
Feedback Loop — למידה מביצועים אמיתיים
מעוף Tech-Lead Israel

תדירות איסוף:
  בית ספר   → כל 3 חודשים (דירוג מורה, נוכחות, שביעות רצון)
  חברה       → כל 6 חודשים (ביצועים, קצב התקדמות)
  מועמד      → כל 6 חודשים (שביעות רצון)

השוואת ציון חיזוי vs ביצועים בפועל → עדכון משקלות אוטומטי.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
import json
import math


# --- מבני נתונים ---

@dataclass
class SchoolFeedback:
    placement_id: str
    candidate_id: str
    school_id: str
    date: str

    teacher_rating: float       # 0-100 — דירוג המורה
    attendance_rate: float      # 0-100 — אחוז נוכחות
    principal_satisfaction: float  # 0-100 — שביעות רצון מנהל
    student_satisfaction: float    # 0-100 — שביעות רצון תלמידים

    @property
    def actual_score(self) -> float:
        return (
            self.teacher_rating * 0.40 +
            self.attendance_rate * 0.20 +
            self.principal_satisfaction * 0.25 +
            self.student_satisfaction * 0.15
        )


@dataclass
class CompanyFeedback:
    placement_id: str
    candidate_id: str
    company_id: str
    date: str

    performance_score: float    # 0-100 — ביצועים
    progression_rate: float     # 0-100 — קצב התקדמות
    manager_satisfaction: float # 0-100 — שביעות רצון מנהל

    @property
    def actual_score(self) -> float:
        return (
            self.performance_score * 0.50 +
            self.progression_rate * 0.30 +
            self.manager_satisfaction * 0.20
        )


@dataclass
class CandidateFeedback:
    placement_id: str
    candidate_id: str
    date: str

    school_satisfaction: float   # 0-100
    company_satisfaction: float  # 0-100
    overall_satisfaction: float  # 0-100

    @property
    def actual_score(self) -> float:
        return (
            self.school_satisfaction * 0.35 +
            self.company_satisfaction * 0.40 +
            self.overall_satisfaction * 0.25
        )


@dataclass
class PlacementRecord:
    """רשומת שיבוץ עם ציון חיזוי וציון בפועל"""
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


# --- מנהל ה-Feedback Loop ---

class FeedbackLoop:
    """
    אוסף משוב, מנתח שגיאות חיזוי, ומעדכן משקלות.
    """

    def __init__(self):
        self.records: List[PlacementRecord] = []
        self.weight_history: List[Dict] = []

    def add_placement(self, record: PlacementRecord):
        self.records.append(record)

    def add_school_feedback(self, placement_id: str, feedback: SchoolFeedback):
        for r in self.records:
            if r.placement_id == placement_id:
                r.school_feedback = feedback
                return
        raise ValueError(f"Placement {placement_id} not found")

    def add_company_feedback(self, placement_id: str, feedback: CompanyFeedback):
        for r in self.records:
            if r.placement_id == placement_id:
                r.company_feedback = feedback
                return
        raise ValueError(f"Placement {placement_id} not found")

    def add_candidate_feedback(self, placement_id: str, feedback: CandidateFeedback):
        for r in self.records:
            if r.placement_id == placement_id:
                r.candidate_feedback = feedback
                return
        raise ValueError(f"Placement {placement_id} not found")

    def get_stats(self) -> Dict:
        """סטטיסטיקות בסיסיות"""
        total = len(self.records)
        with_feedback = [r for r in self.records if r.actual_score is not None]
        full_feedback = [r for r in self.records if r.has_full_feedback]

        errors = [abs(r.prediction_error) for r in with_feedback if r.prediction_error is not None]
        mae = round(sum(errors) / len(errors), 2) if errors else None

        return {
            "total_placements": total,
            "with_some_feedback": len(with_feedback),
            "with_full_feedback": len(full_feedback),
            "mean_absolute_error": mae,
            "phase": self._get_phase(),
        }

    def _get_phase(self) -> str:
        n = len(self.records)
        if n < 50:
            return "synthetic"
        elif n < 200:
            return "mixed"
        else:
            return "real_data"

    def analyze_errors(self) -> Dict:
        """
        מנתח את שגיאות החיזוי ומזהה תבניות.
        האם אנחנו מנפחים? מזלזלים? באיזה סוג שיבוצים?
        """
        records_with_error = [
            r for r in self.records
            if r.prediction_error is not None
        ]

        if not records_with_error:
            return {"message": "אין מספיק נתונים לניתוח"}

        errors = [r.prediction_error for r in records_with_error]
        avg_error = sum(errors) / len(errors)

        # הטיה מערכתית
        bias = "מנפחים ציונים" if avg_error > 5 else \
               "מזלזלים בציונים" if avg_error < -5 else \
               "ניבוי מאוזן"

        # שיבוצים עם שגיאה גדולה
        large_errors = [
            {
                "placement_id": r.placement_id,
                "predicted": r.predicted_score,
                "actual": r.actual_score,
                "error": r.prediction_error,
            }
            for r in records_with_error
            if abs(r.prediction_error) > 15
        ]

        return {
            "n_analyzed": len(records_with_error),
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
        """
        מציע עדכון משקלות בהתבסס על שגיאות החיזוי.
        שיטה: Gradient-like adjustment.
        """
        analysis = self.analyze_errors()

        if "message" in analysis:
            return {"message": analysis["message"]}

        avg_error = analysis["avg_error"]
        learning_rate = 0.02

        # עדכון פשוט — אם מנפחים, הורד A; אם מזלזלים, הורד B
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
        """
        מייצא נתונים לאימון מחדש של המשקלות.
        """
        return [
            {
                "placement_id": r.placement_id,
                "predicted_score": r.predicted_score,
                "actual_score": r.actual_score,
                "error": r.prediction_error,
                "has_full_feedback": r.has_full_feedback,
            }
            for r in self.records
            if r.actual_score is not None
        ]


# --- דמו ---
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    print("Feedback Loop — Demo")
    print("=" * 40)

    loop = FeedbackLoop()

    # הוספת שיבוצים עם ציונים מחוזים
    placements_data = [
        ("P001", "C001", "S001", "CO001", 75.0),
        ("P002", "C002", "S002", "CO002", 82.0),
        ("P003", "C003", "S001", "CO003", 68.0),
    ]

    for pid, cid, sid, coid, score in placements_data:
        loop.add_placement(PlacementRecord(pid, cid, sid, coid, score))

    # משוב בית ספר
    loop.add_school_feedback("P001", SchoolFeedback(
        "P001", "C001", "S001", "2026-03-01",
        teacher_rating=80, attendance_rate=90,
        principal_satisfaction=75, student_satisfaction=85
    ))

    # משוב חברה
    loop.add_company_feedback("P001", CompanyFeedback(
        "P001", "C001", "CO001", "2026-06-01",
        performance_score=70, progression_rate=65,
        manager_satisfaction=75
    ))

    # משוב מועמד
    loop.add_candidate_feedback("P001", CandidateFeedback(
        "P001", "C001", "2026-06-01",
        school_satisfaction=80, company_satisfaction=75,
        overall_satisfaction=78
    ))

    print("\nסטטיסטיקות:")
    stats = loop.get_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\nניתוח שגיאות:")
    errors = loop.analyze_errors()
    for k, v in errors.items():
        print(f"  {k}: {v}")

    print("\nהמלצת עדכון משקלות:")
    suggestion = loop.suggest_weight_update()
    for k, v in suggestion.items():
        print(f"  {k}: {v}")
