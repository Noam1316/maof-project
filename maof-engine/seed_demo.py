"""
Seed Demo Data — מעוף Tech-Lead Israel
מריץ פעם אחת כדי לאכלס את Supabase בנתוני הדמו.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database.client import is_connected
from database.repository import upsert_candidate, upsert_school, upsert_company
from models.candidate import AcademicBackground, MilitaryRole

CANDIDATES = [
    {
        "id": "DEMO_001", "name": "נועה לוי",
        "eli5_score": 88.0, "subject": "סייבר",
        "additional_subjects": ["מדעי מחשב", "פייתון"],
        "distance_km": 12.0, "family_status_score": 75.0,
        "commitment_score": 92.0, "career_switches": 0,
        "willing_periphery": True, "tech_test_score": 94.0,
        "academic_background": "tech_unit",
        "independent_courses": 3, "promotion_rate": 85.0,
        "military_role": "tech_lead", "team_size": 8,
        "conflict_resolution_score": 80.0,
        "preferred_company_size": "enterprise", "work_style": "agile",
        "preferred_location": "תל אביב", "willing_relocate": False,
        "tech_stack": ["Python", "C++", "Cybersecurity"],
        "years_experience": 3.0,
    },
    {
        "id": "DEMO_002", "name": "יובל כהן",
        "eli5_score": 82.0, "subject": "פייתון",
        "additional_subjects": ["מדעי מחשב"],
        "distance_km": 8.0, "family_status_score": 80.0,
        "commitment_score": 87.0, "career_switches": 1,
        "willing_periphery": True, "tech_test_score": 91.0,
        "academic_background": "tech_unit",
        "independent_courses": 4, "promotion_rate": 90.0,
        "military_role": "unit_commander", "team_size": 12,
        "conflict_resolution_score": 88.0,
        "preferred_company_size": "enterprise", "work_style": "agile",
        "preferred_location": "תל אביב", "willing_relocate": True,
        "tech_stack": ["Python", "Machine Learning", "TypeScript"],
        "years_experience": 3.5,
    },
    {
        "id": "DEMO_003", "name": "תמר בן-דוד",
        "eli5_score": 85.0, "subject": "מדעי מחשב",
        "additional_subjects": ["פייתון", "מתמטיקה"],
        "distance_km": 25.0, "family_status_score": 65.0,
        "commitment_score": 83.0, "career_switches": 0,
        "willing_periphery": True, "tech_test_score": 89.0,
        "academic_background": "tech_unit",
        "independent_courses": 5, "promotion_rate": 78.0,
        "military_role": "tech_lead", "team_size": 6,
        "conflict_resolution_score": 75.0,
        "preferred_company_size": "mid", "work_style": "agile",
        "preferred_location": "חיפה", "willing_relocate": True,
        "tech_stack": ["Python", "Data Science", "SQL"],
        "years_experience": 2.5,
    },
    {
        "id": "DEMO_004", "name": "אור שמיר",
        "eli5_score": 78.0, "subject": "פייתון",
        "additional_subjects": ["מדעי מחשב"],
        "distance_km": 15.0, "family_status_score": 85.0,
        "commitment_score": 88.0, "career_switches": 1,
        "willing_periphery": False, "tech_test_score": 86.0,
        "academic_background": "tech_unit",
        "independent_courses": 3, "promotion_rate": 82.0,
        "military_role": "tech_lead", "team_size": 5,
        "conflict_resolution_score": 82.0,
        "preferred_company_size": "enterprise", "work_style": "hybrid",
        "preferred_location": "תל אביב", "willing_relocate": False,
        "tech_stack": ["Python", "React", "Node.js"],
        "years_experience": 3.0,
    },
    {
        "id": "DEMO_005", "name": "רון מזרחי",
        "eli5_score": 72.0, "subject": "מתמטיקה",
        "additional_subjects": ["פיזיקה"],
        "distance_km": 35.0, "family_status_score": 70.0,
        "commitment_score": 78.0, "career_switches": 2,
        "willing_periphery": True, "tech_test_score": 83.0,
        "academic_background": "bagrut_math_cs",
        "independent_courses": 2, "promotion_rate": 70.0,
        "military_role": "soldier", "team_size": 3,
        "conflict_resolution_score": 72.0,
        "preferred_company_size": "mid", "work_style": "agile",
        "preferred_location": "חיפה", "willing_relocate": True,
        "tech_stack": ["JavaScript", "React", "Node.js"],
        "years_experience": 1.5,
    },
    {
        "id": "DEMO_006", "name": "מיכל ראובן",
        "eli5_score": 68.0, "subject": "מדעי מחשב",
        "additional_subjects": ["פייתון"],
        "distance_km": 20.0, "family_status_score": 60.0,
        "commitment_score": 72.0, "career_switches": 1,
        "willing_periphery": False, "tech_test_score": 77.0,
        "academic_background": "self_taught",
        "independent_courses": 6, "promotion_rate": 65.0,
        "military_role": "soldier", "team_size": 2,
        "conflict_resolution_score": 68.0,
        "preferred_company_size": "startup", "work_style": "agile",
        "preferred_location": "תל אביב", "willing_relocate": False,
        "tech_stack": ["React", "TypeScript", "CSS"],
        "years_experience": 1.0,
    },
]

SCHOOLS = [
    {
        "id": "S_SDEROT", "name": "תיכון שדרות",
        "location": "שדרות", "lat": 31.52, "lng": 34.59,
        "required_subjects": ["סייבר", "מדעי מחשב"],
        "grade_levels": ["י", "יא", "יב"],
        "socioeconomic_rank": 3, "nurturing_index": 8,
        "months_without_teacher": 8, "budget_available": True,
        "capacity": 2,
    },
    {
        "id": "S_HADERA", "name": "תיכון חדרה",
        "location": "חדרה", "lat": 32.44, "lng": 34.91,
        "required_subjects": ["פייתון", "מתמטיקה"],
        "grade_levels": ["ט", "י", "יא", "יב"],
        "socioeconomic_rank": 6, "nurturing_index": 5,
        "months_without_teacher": 4, "budget_available": True,
        "capacity": 2,
    },
    {
        "id": "S_BEERSHEVA", "name": "תיכון טכנולוגי באר שבע",
        "location": "באר שבע", "lat": 31.24, "lng": 34.79,
        "required_subjects": ["פייתון", "מדעי מחשב", "אלקטרוניקה"],
        "grade_levels": ["ז", "ח", "ט", "י", "יא", "יב"],
        "socioeconomic_rank": 4, "nurturing_index": 7,
        "months_without_teacher": 6, "budget_available": True,
        "capacity": 3,
    },
]

COMPANIES = [
    {
        "id": "CO_MOBILEYE", "name": "Mobileye",
        "location": "ירושלים", "lat": 31.78, "lng": 35.22,
        "size": "enterprise", "work_style": "agile",
        "tech_stack": ["Python", "C++", "AI", "Computer Vision"],
        "open_positions": 3, "urgency_score": 85.0,
        "willing_station_b": True, "placement_fee_paid": False,
    },
    {
        "id": "CO_CHECKPOINT", "name": "Check Point",
        "location": "תל אביב", "lat": 32.08, "lng": 34.78,
        "size": "enterprise", "work_style": "agile",
        "tech_stack": ["Python", "C", "Cybersecurity", "Linux"],
        "open_positions": 4, "urgency_score": 90.0,
        "willing_station_b": True, "placement_fee_paid": False,
    },
    {
        "id": "CO_MSFT", "name": "Microsoft Israel",
        "location": "הרצליה", "lat": 32.16, "lng": 34.84,
        "size": "enterprise", "work_style": "hybrid",
        "tech_stack": ["Python", "TypeScript", "Azure", "React"],
        "open_positions": 5, "urgency_score": 78.0,
        "willing_station_b": True, "placement_fee_paid": False,
    },
]


def seed():
    if not is_connected():
        print("ERROR: Supabase not connected — check .env")
        return

    print("Seeding Supabase demo data...")

    for c in CANDIDATES:
        upsert_candidate(c)
        print(f"  + candidate: {c['id']}")

    for s in SCHOOLS:
        upsert_school(s)
        print(f"  + school: {s['id']}")

    for co in COMPANIES:
        upsert_company(co)
        print(f"  + company: {co['id']}")

    print(f"\nDone: {len(CANDIDATES)} candidates, {len(SCHOOLS)} schools, {len(COMPANIES)} companies")


if __name__ == "__main__":
    seed()
