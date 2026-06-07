"""
ציון A — כושר הוראה (0-100)
מעוף Tech-Lead Israel

מבנה:
  ELI5          35%
  התאמת מקצוע   25%
  שימור          25%
  השפעה          15%
"""

from models.candidate import Candidate, AcademicBackground
from models.school import School
from nlp.semantic_match import subject_semantic_score
from nlp.eli5_scorer import compute_eli5_score
from feedback.weight_store import load_weights

_W = load_weights()["score_a"]


# --- טבלת מרחק ---
def distance_score(km: float, willing_periphery: bool) -> float:
    if willing_periphery:
        return 100.0
    if km <= 10:
        return 100.0
    elif km <= 25:
        return 80.0
    elif km <= 40:
        return 60.0
    elif km <= 60:
        return 35.0
    else:
        return 10.0


# --- שימור (25%) ---
def retention_score(candidate: Candidate, school: School) -> float:
    dist = distance_score(candidate.distance_km, candidate.willing_periphery)
    family = candidate.family_status_score
    commitment = candidate.commitment_score

    # יציבות קריירה — פחות החלפות = ציון גבוה יותר
    stability = max(0, 100 - candidate.career_switches * 15)

    return (
        dist * 0.35 +
        family * 0.25 +
        commitment * 0.25 +
        stability * 0.15
    )


# --- התאמת מקצוע (25%) ---
def subject_match_score(candidate: Candidate, school: School) -> float:
    # כל מקצועות המועמד
    candidate_subjects = [candidate.subject] + (candidate.additional_subjects or [])

    # התאמה סמנטית — עברית/אנגלית + נרדפות
    semantic_match = subject_semantic_score(candidate_subjects, school.required_subjects)

    # גמישות מקצועית — כמה מקצועות נוספים יכול ללמד
    flexibility = min(100.0, len(candidate.additional_subjects) * 20)

    return (
        semantic_match * 0.80 +
        flexibility * 0.20
    )


# --- השפעה (15%) ---
def impact_score(school: School) -> float:
    # פריפריה — דירוג סוציו-אקונומי הפוך (1=עני=ציון גבוה)
    periphery = (10 - school.socioeconomic_rank) * 10 + 10

    # מדד טיפוח — הפוך
    nurturing = (10 - school.nurturing_index) * 10 + 10

    # דחיפות — חודשים ללא מורה
    urgency = min(100, school.months_without_teacher * 10)

    return (
        periphery * 0.40 +
        nurturing * 0.30 +
        urgency * 0.30
    )


# --- ציון A סופי ---
def calculate_score_a(candidate: Candidate, school: School) -> float:
    eli5 = compute_eli5_score(candidate.eli5_text, candidate.eli5_topic, candidate.eli5_score)
    subject = subject_match_score(candidate, school)
    retention = retention_score(candidate, school)
    impact = impact_score(school)

    score = (
        eli5      * _W["eli5"] +
        subject   * _W["subject"] +
        retention * _W["retention"] +
        impact    * _W["impact"]
    )

    return round(score, 2)


def calculate_score_a_detailed(candidate: Candidate, school: School) -> dict:
    eli5 = compute_eli5_score(candidate.eli5_text, candidate.eli5_topic, candidate.eli5_score)
    subject = subject_match_score(candidate, school)
    retention = retention_score(candidate, school)
    impact = impact_score(school)

    total = round(
        eli5      * _W["eli5"] +
        subject   * _W["subject"] +
        retention * _W["retention"] +
        impact    * _W["impact"],
    2)

    return {
        "total": total,
        "components": {
            "eli5": {"raw": round(eli5, 2), "weight": 0.35, "weighted": round(eli5 * 0.35, 2)},
            "subject_match": {"raw": round(subject, 2), "weight": 0.25, "weighted": round(subject * 0.25, 2)},
            "retention": {"raw": round(retention, 2), "weight": 0.25, "weighted": round(retention * 0.25, 2)},
            "impact": {"raw": round(impact, 2), "weight": 0.15, "weighted": round(impact * 0.15, 2)},
        },
        "explanation": _explain_score_a(eli5, subject, retention, impact, total, candidate, school),
    }


def _explain_score_a(eli5, subject, retention, impact, total, candidate, school) -> str:
    parts = []
    parts.append(f"ציון A = {total}")
    parts.append(f"ELI5={eli5:.0f}×35% + מקצוע={subject:.0f}×25% + שימור={retention:.0f}×25% + השפעה={impact:.0f}×15%")

    best = max([("ELI5", eli5), ("התאמת מקצוע", subject), ("שימור", retention), ("השפעה", impact)], key=lambda x: x[1])
    worst = min([("ELI5", eli5), ("התאמת מקצוע", subject), ("שימור", retention), ("השפעה", impact)], key=lambda x: x[1])
    parts.append(f"חוזק: {best[0]} ({best[1]:.0f})")
    parts.append(f"חולשה: {worst[0]} ({worst[1]:.0f})")

    return " | ".join(parts)
