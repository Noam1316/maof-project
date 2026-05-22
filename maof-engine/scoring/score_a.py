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
    # התאמת מקצוע עיקרי
    primary_match = 100.0 if candidate.subject in school.required_subjects else 0.0

    # גמישות מקצועית — כמה מקצועות נוספים
    flexibility = min(100.0, len(candidate.additional_subjects) * 20)

    # התאמת רמה — placeholder ל-vector similarity עתידי
    level_match = 80.0  # TODO: sentence-transformers

    return (
        primary_match * 0.50 +
        level_match * 0.30 +
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
    eli5 = candidate.eli5_score
    subject = subject_match_score(candidate, school)
    retention = retention_score(candidate, school)
    impact = impact_score(school)

    score = (
        eli5 * 0.35 +
        subject * 0.25 +
        retention * 0.25 +
        impact * 0.15
    )

    return round(score, 2)
