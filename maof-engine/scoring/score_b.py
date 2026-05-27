"""
ציון B — התאמה לחברה (0-100)
מעוף Tech-Lead Israel

מבנה:
  מיומנות טכנית    35%
  פוטנציאל צמיחה   25%
  כישורים רכים     25%
  התאמה תרבותית   15%
"""

from models.candidate import Candidate, AcademicBackground, MilitaryRole
from models.company import Company
from nlp.semantic_match import tech_stack_semantic_score


# --- טבלת רקע אקדמי ---
ACADEMIC_SCORES = {
    AcademicBackground.ATUDA: 100,
    AcademicBackground.WARRIORS_TECH: 95,
    AcademicBackground.TECH_UNIT: 95,
    AcademicBackground.PARTIAL_DEGREE: 85,
    AcademicBackground.BAGRUT_MATH_CS: 80,
    AcademicBackground.BAGRUT_MATH: 65,
    AcademicBackground.SELF_TAUGHT: 55,
    AcademicBackground.REGULAR_BAGRUT: 45,
}

# --- טבלת מנהיגות ---
LEADERSHIP_SCORES = {
    MilitaryRole.UNIT_COMMANDER: 100,
    MilitaryRole.TECH_LEAD: 85,
    MilitaryRole.MENTOR: 70,
    MilitaryRole.SOLDIER: 45,
}


# --- Tech Stack Match ---
def tech_stack_match(candidate: Candidate, company: Company) -> float:
    if not company.tech_stack:
        return 80.0
    if not candidate.tech_stack:
        return 30.0
    # Semantic match — עברית/אנגלית + נרדפות טכנולוגיות
    return tech_stack_semantic_score(candidate.tech_stack, company.tech_stack)


# --- מיומנות טכנית (35%) ---
def tech_skills_score(candidate: Candidate, company: Company) -> float:
    tech_test = candidate.tech_test_score
    stack_match = tech_stack_match(candidate, company)
    academic = ACADEMIC_SCORES[candidate.academic_background]

    return (
        tech_test * 0.50 +
        stack_match * 0.30 +
        academic * 0.20
    )


# --- פוטנציאל צמיחה (25%) ---
def growth_potential_score(candidate: Candidate) -> float:
    # הערה עיצובית: career_switches כאן חיובי (חברה = adaptability, ניסיון מגוון)
    # לעומת score_a.retention_score שמענישה career_switches (בית ספר = יציבות)
    # זה כוונתי — שתי הפרספקטיבות שונות מטבען
    academic = ACADEMIC_SCORES[candidate.academic_background]
    courses = min(100, candidate.independent_courses * 15)
    promotion = candidate.promotion_rate
    learning_agility = min(100, candidate.independent_courses * 20 + candidate.career_switches * 15)

    return (
        academic * 0.25 +
        courses * 0.30 +
        promotion * 0.25 +
        learning_agility * 0.20
    )


# --- כישורים רכים (25%) ---
def soft_skills_score(candidate: Candidate) -> float:
    leadership = LEADERSHIP_SCORES[candidate.military_role]
    teamwork = min(100, candidate.team_size * 10)
    communication = candidate.eli5_score  # מציון A
    conflict = candidate.conflict_resolution_score

    return (
        leadership * 0.35 +
        teamwork * 0.30 +
        communication * 0.20 +
        conflict * 0.15
    )


# --- התאמה תרבותית (15%) ---
SIZE_PROXIMITY = {
    ("startup", "startup"): 100, ("startup", "mid"): 75, ("startup", "enterprise"): 40,
    ("mid", "startup"): 75, ("mid", "mid"): 100, ("mid", "enterprise"): 70,
    ("enterprise", "startup"): 40, ("enterprise", "mid"): 70, ("enterprise", "enterprise"): 100,
}


def cultural_fit_score(candidate: Candidate, company: Company) -> float:
    size_match = SIZE_PROXIMITY.get(
        (candidate.preferred_company_size, company.size), 50.0
    )
    style_match = 100.0 if candidate.work_style == company.work_style else 50.0
    location_match = 100.0 if (
        candidate.preferred_location == company.location or
        candidate.willing_relocate
    ) else 30.0

    return (
        size_match * 0.35 +
        style_match * 0.35 +
        location_match * 0.30
    )


# --- ציון B סופי ---
def calculate_score_b(candidate: Candidate, company: Company) -> float:
    tech = tech_skills_score(candidate, company)
    growth = growth_potential_score(candidate)
    soft = soft_skills_score(candidate)
    cultural = cultural_fit_score(candidate, company)

    score = (
        tech * 0.35 +
        growth * 0.25 +
        soft * 0.25 +
        cultural * 0.15
    )

    return round(score, 2)


def calculate_score_b_detailed(candidate: Candidate, company: Company) -> dict:
    tech = tech_skills_score(candidate, company)
    growth = growth_potential_score(candidate)
    soft = soft_skills_score(candidate)
    cultural = cultural_fit_score(candidate, company)

    total = round(tech * 0.35 + growth * 0.25 + soft * 0.25 + cultural * 0.15, 2)

    return {
        "total": total,
        "components": {
            "tech_skills": {"raw": round(tech, 2), "weight": 0.35, "weighted": round(tech * 0.35, 2)},
            "growth_potential": {"raw": round(growth, 2), "weight": 0.25, "weighted": round(growth * 0.25, 2)},
            "soft_skills": {"raw": round(soft, 2), "weight": 0.25, "weighted": round(soft * 0.25, 2)},
            "cultural_fit": {"raw": round(cultural, 2), "weight": 0.15, "weighted": round(cultural * 0.15, 2)},
        },
        "explanation": _explain_score_b(tech, growth, soft, cultural, total, candidate, company),
    }


def _explain_score_b(tech, growth, soft, cultural, total, candidate, company) -> str:
    parts = []
    parts.append(f"ציון B = {total}")
    parts.append(f"טכני={tech:.0f}×35% + צמיחה={growth:.0f}×25% + רך={soft:.0f}×25% + תרבות={cultural:.0f}×15%")

    best = max([("מיומנות טכנית", tech), ("פוטנציאל צמיחה", growth), ("כישורים רכים", soft), ("התאמה תרבותית", cultural)], key=lambda x: x[1])
    worst = min([("מיומנות טכנית", tech), ("פוטנציאל צמיחה", growth), ("כישורים רכים", soft), ("התאמה תרבותית", cultural)], key=lambda x: x[1])
    parts.append(f"חוזק: {best[0]} ({best[1]:.0f})")
    parts.append(f"חולשה: {worst[0]} ({worst[1]:.0f})")

    return " | ".join(parts)
