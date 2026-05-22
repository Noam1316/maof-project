"""
ציון C — Three-Way Score (0-100)
מעוף Tech-Lead Israel

C = (min(A,B) + דחיפות + קרבה + נכונות) / 4

ניקוד דחיפות:
  בית ספר ללא מורה + חברה עם משרה פתוחה = 100
  אחד מהם דחוף                             = 60
  אף אחד לא דחוף                           = 30

ניקוד נכונות — דינמי לפי שלב:
  0-50   שיבוצים → מועמד בלבד
  50-200 שיבוצים → מועמד + חברה
  200+   שיבוצים → מועמד + חברה + בית ספר
"""

from models.candidate import Candidate
from models.school import School
from models.company import Company
from scoring.score_a import distance_score


def urgency_score(school: School, company: Company) -> float:
    school_urgent = school.months_without_teacher >= 3
    company_urgent = company.urgency_score >= 60

    if school_urgent and company_urgent:
        return 100.0
    elif school_urgent or company_urgent:
        return 60.0
    else:
        return 30.0


def proximity_score(candidate: Candidate) -> float:
    return distance_score(candidate.distance_km, candidate.willing_periphery)


def willingness_score(
    candidate_willing: bool,
    company_willing: bool,
    school_willing: bool,
    total_placements: int
) -> float:
    if total_placements < 50:
        # שלב ראשון — מועמד בלבד
        return 100.0 if candidate_willing else 0.0
    elif total_placements < 200:
        # שלב שני — מועמד + חברה
        if candidate_willing and company_willing:
            return 100.0
        elif candidate_willing or company_willing:
            return 50.0
        return 0.0
    else:
        # שלב שלישי — כולם
        score = 0.0
        if candidate_willing:
            score += 34.0
        if company_willing:
            score += 33.0
        if school_willing:
            score += 33.0
        return score


def calculate_score_c(
    score_a: float,
    score_b: float,
    candidate: Candidate,
    school: School,
    company: Company,
    total_placements: int = 0,
    candidate_willing: bool = True,
    company_willing: bool = True,
    school_willing: bool = True
) -> float:
    min_ab = min(score_a, score_b)
    urgency = urgency_score(school, company)
    proximity = proximity_score(candidate)
    willingness = willingness_score(
        candidate_willing,
        company_willing,
        school_willing,
        total_placements
    )

    score = (min_ab + urgency + proximity + willingness) / 4
    return round(score, 2)
