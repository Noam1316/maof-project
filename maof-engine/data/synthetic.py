"""
Synthetic Data Generator — Dual Benchmark
מעוף Tech-Lead Israel

שלב 0-50 שיבוצים: נתונים סינתטיים לאימון
"""

import random
from models.candidate import Candidate, AcademicBackground, MilitaryRole
from models.school import School
from models.company import Company


SUBJECTS = ["סייבר", "פייתון", "מתמטיקה", "פיזיקה", "מדעי מחשב", "אלקטרוניקה"]
LOCATIONS = ["תל אביב", "ירושלים", "חיפה", "באר שבע", "אשדוד", "נתניה"]
TECH_STACKS = ["Python", "JavaScript", "React", "Node.js", "TypeScript", "Java", "C++"]
SIZES = ["startup", "mid", "enterprise"]
STYLES = ["agile", "waterfall", "hybrid"]


def generate_candidate(id: str) -> Candidate:
    return Candidate(
        id=id,
        name=f"מועמד {id}",
        eli5_score=random.uniform(50, 100),
        subject=random.choice(SUBJECTS),
        additional_subjects=random.sample(SUBJECTS, random.randint(0, 3)),
        distance_km=random.uniform(0, 80),
        family_status_score=random.uniform(40, 100),
        commitment_score=random.uniform(50, 100),
        career_switches=random.randint(0, 4),
        willing_periphery=random.choice([True, False]),
        tech_test_score=random.uniform(50, 100),
        academic_background=random.choice(list(AcademicBackground)),
        independent_courses=random.randint(0, 5),
        promotion_rate=random.uniform(40, 100),
        military_role=random.choice(list(MilitaryRole)),
        team_size=random.randint(0, 20),
        conflict_resolution_score=random.uniform(40, 100),
        preferred_company_size=random.choice(SIZES),
        work_style=random.choice(STYLES),
        preferred_location=random.choice(LOCATIONS),
        willing_relocate=random.choice([True, False]),
        tech_stack=random.sample(TECH_STACKS, random.randint(1, 4)),
        years_experience=random.uniform(0, 5),
    )


def generate_school(id: str) -> School:
    location = random.choice(LOCATIONS)
    return School(
        id=id,
        name=f"בית ספר {id}",
        location=location,
        lat=31.5 + random.uniform(-1, 1),
        lng=34.8 + random.uniform(-1, 1),
        required_subjects=random.sample(SUBJECTS, random.randint(1, 3)),
        grade_levels=random.sample(["ז", "ח", "ט", "י", "יא", "יב"], random.randint(2, 4)),
        socioeconomic_rank=random.randint(1, 10),
        nurturing_index=random.randint(1, 10),
        months_without_teacher=random.randint(0, 12),
        budget_available=random.choice([True, False]),
    )


def generate_company(id: str) -> Company:
    location = random.choice(LOCATIONS)
    return Company(
        id=id,
        name=f"חברת הייטק {id}",
        location=location,
        lat=31.5 + random.uniform(-1, 1),
        lng=34.8 + random.uniform(-1, 1),
        size=random.choice(SIZES),
        work_style=random.choice(STYLES),
        tech_stack=random.sample(TECH_STACKS, random.randint(2, 5)),
        open_positions=random.randint(0, 5),
        urgency_score=random.uniform(0, 100),
        willing_station_b=True,
        placement_fee_paid=False,
    )


def generate_dataset(n_candidates=10, n_schools=5, n_companies=5):
    candidates = [generate_candidate(f"C{i+1:03d}") for i in range(n_candidates)]
    schools = [generate_school(f"S{i+1:03d}") for i in range(n_schools)]
    companies = [generate_company(f"CO{i+1:03d}") for i in range(n_companies)]
    return candidates, schools, companies
