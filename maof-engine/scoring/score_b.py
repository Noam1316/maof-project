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
    candidate_set = set(t.lower() for t in candidate.tech_stack)
    company_set = set(t.lower() for t in company.tech_stack)
    overlap = len(candidate_set & company_set)
    return min(100.0, (overlap / len(company_set)) * 100)


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
    academic = ACADEMIC_SCORES[candidate.academic_background]
    courses = min(100, candidate.independent_courses * 15)
    promotion = candidate.promotion_rate

    # adaptive test — מהמבחן הטכני (שאלה כמה הגיע)
    adaptive = candidate.tech_test_score  # placeholder

    return (
        academic * 0.25 +
        courses * 0.30 +
        promotion * 0.25 +
        adaptive * 0.20
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
def cultural_fit_score(candidate: Candidate, company: Company) -> float:
    size_match = 100.0 if candidate.preferred_company_size == company.size else 50.0
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
