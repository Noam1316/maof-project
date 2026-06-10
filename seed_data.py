"""
seed_data.py — נתוני seed ישראליים אמיתיים למערכת מעוף
מריץ: python seed_data.py
"""

import sys
import io
import requests
import json
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = "https://maof-project.onrender.com/api/v1"

# ── wake up Render ──────────────────────────────────────────────
print(">> מעיר את השרת...")
for i in range(3):
    try:
        r = requests.get(f"{BASE}/health", timeout=30)
        if r.status_code == 200:
            print(f"   OK שרת פעיל: {r.json()}")
            break
    except Exception as e:
        print(f"   ניסיון {i+1}: {e}")
        time.sleep(5)

# ── מועמדים ─────────────────────────────────────────────────────
CANDIDATES = [
    {
        "id": "CAND_YOAV_COHEN",
        "name": "יואב כהן",
        "subject": "סייבר",
        "additional_subjects": ["מדעי המחשב", "פייתון"],
        "eli5_score": 82,
        "eli5_topic": "סייבר",
        "distance_km": 4.5,
        "family_status_score": 70,
        "commitment_score": 88,
        "career_switches": 1,
        "willing_periphery": False,
        "tech_test_score": 91,
        "academic_background": "tech_unit",     # יחידה 8200
        "independent_courses": 6,
        "promotion_rate": 85,
        "military_role": "tech_lead",
        "team_size": 8,
        "conflict_resolution_score": 78,
        "preferred_company_size": "enterprise",
        "work_style": "agile",
        "preferred_location": "תל אביב",
        "willing_relocate": False,
        "tech_stack": ["Python", "C", "Linux", "Network Security"],
        "years_experience": 3.5,
        "systemic_score": 88,
        "code_score": 90,
    },
    {
        "id": "CAND_MICHAL_LEVI",
        "name": "מיכל לוי",
        "subject": "מתמטיקה",
        "additional_subjects": ["פיזיקה"],
        "eli5_score": 78,
        "eli5_topic": "מתמטיקה",
        "distance_km": 12.0,
        "family_status_score": 60,
        "commitment_score": 92,
        "career_switches": 0,
        "willing_periphery": True,
        "tech_test_score": 72,
        "academic_background": "bagrut_math_cs",   # בגרות 5 יח' + מחשב
        "independent_courses": 3,
        "promotion_rate": 90,
        "military_role": "unit_commander",          # מפקד כיתה בגולני
        "team_size": 12,
        "conflict_resolution_score": 85,
        "preferred_company_size": "mid",
        "work_style": "hybrid",
        "preferred_location": "חיפה",
        "willing_relocate": True,
        "tech_stack": ["Python", "MATLAB", "Excel"],
        "years_experience": 2.5,
        "systemic_score": 75,
        "code_score": 68,
    },
    {
        "id": "CAND_ROI_AVIV",
        "name": "רועי אביב",
        "subject": "מדעי המחשב",
        "additional_subjects": ["פייתון", "סייבר"],
        "eli5_score": 74,
        "eli5_topic": "מדעי המחשב",
        "distance_km": 8.0,
        "family_status_score": 80,
        "commitment_score": 75,
        "career_switches": 2,
        "willing_periphery": False,
        "tech_test_score": 85,
        "academic_background": "warriors_tech",     # לוחמים להייטק
        "independent_courses": 8,
        "promotion_rate": 72,
        "military_role": "tech_lead",               # יחידה 81
        "team_size": 5,
        "conflict_resolution_score": 70,
        "preferred_company_size": "startup",
        "work_style": "agile",
        "preferred_location": "ירושלים",
        "willing_relocate": False,
        "tech_stack": ["Python", "JavaScript", "React", "Docker"],
        "years_experience": 2.0,
        "systemic_score": 82,
        "code_score": 87,
    },
    {
        "id": "CAND_SHIRA_MIZRAHI",
        "name": "שירה מזרחי",
        "subject": "ביולוגיה",
        "additional_subjects": ["כימיה", "מדעים"],
        "eli5_score": 88,
        "eli5_topic": "ביולוגיה",
        "distance_km": 3.0,
        "family_status_score": 65,
        "commitment_score": 95,
        "career_switches": 0,
        "willing_periphery": True,
        "tech_test_score": 65,
        "academic_background": "partial_degree",    # שנת לימודים רפואה
        "independent_courses": 2,
        "promotion_rate": 88,
        "military_role": "mentor",                  # חונכת / מדריכה
        "team_size": 6,
        "conflict_resolution_score": 91,
        "preferred_company_size": "mid",
        "work_style": "hybrid",
        "preferred_location": "באר שבע",
        "willing_relocate": True,
        "tech_stack": ["Python", "R", "Excel"],
        "years_experience": 1.5,
        "systemic_score": 70,
        "code_score": 60,
    },
    {
        "id": "CAND_ADAM_PERETZ",
        "name": "אדם פרץ",
        "subject": "פיזיקה",
        "additional_subjects": ["מתמטיקה"],
        "eli5_score": 71,
        "eli5_topic": "פיזיקה",
        "distance_km": 18.0,
        "family_status_score": 75,
        "commitment_score": 80,
        "career_switches": 1,
        "willing_periphery": True,
        "tech_test_score": 78,
        "academic_background": "bagrut_math",       # 5 יחידות מתמטיקה
        "independent_courses": 4,
        "promotion_rate": 68,
        "military_role": "soldier",
        "team_size": 3,
        "conflict_resolution_score": 72,
        "preferred_company_size": "enterprise",
        "work_style": "waterfall",
        "preferred_location": "נתניה",
        "willing_relocate": False,
        "tech_stack": ["C++", "Python", "Embedded"],
        "years_experience": 2.0,
        "systemic_score": 76,
        "code_score": 79,
    },
]

# ── בתי ספר ──────────────────────────────────────────────────────
SCHOOLS = [
    {
        "id": "SCH_AMAL_TLV",
        "name": "תיכון עמל א' תל אביב",
        "location": "תל אביב",
        "lat": 32.0853,
        "lng": 34.7818,
        "required_subjects": ["מדעי המחשב", "סייבר", "פייתון"],
        "grade_levels": ["ט'", "י'", "י\"א", "י\"ב"],
        "socioeconomic_rank": 5,
        "nurturing_index": 4,
        "months_without_teacher": 8,
        "budget_available": True,
        "capacity": 2,
    },
    {
        "id": "SCH_KATZIR_NAHARIYA",
        "name": "תיכון קציר נהריה",
        "location": "נהריה",
        "lat": 33.0068,
        "lng": 35.0978,
        "required_subjects": ["מתמטיקה", "פיזיקה", "מדעים"],
        "grade_levels": ["ז'", "ח'", "ט'", "י'"],
        "socioeconomic_rank": 3,
        "nurturing_index": 3,
        "months_without_teacher": 14,
        "budget_available": True,
        "capacity": 2,
    },
    {
        "id": "SCH_WEIZMANN_RISHON",
        "name": "תיכון ויצמן ראשון לציון",
        "location": "ראשון לציון",
        "lat": 31.9730,
        "lng": 34.7925,
        "required_subjects": ["מדעי המחשב", "פייתון", "מתמטיקה"],
        "grade_levels": ["י'", "י\"א", "י\"ב"],
        "socioeconomic_rank": 6,
        "nurturing_index": 5,
        "months_without_teacher": 5,
        "budget_available": True,
        "capacity": 1,
    },
]

# ── חברות ────────────────────────────────────────────────────────
COMPANIES = [
    {
        "id": "CO_MICROSOFT_IL",
        "name": "Microsoft Israel",
        "location": "הרצליה",
        "lat": 32.1663,
        "lng": 34.8127,
        "size": "enterprise",
        "work_style": "agile",
        "tech_stack": ["Python", "Azure", "TypeScript", "C#", "Docker"],
        "open_positions": 12,
        "urgency_score": 85,
        "willing_station_b": True,
        "placement_fee_paid": False,
    },
    {
        "id": "CO_CHECKPOINT_IL",
        "name": "Check Point Technologies",
        "location": "תל אביב",
        "lat": 32.0700,
        "lng": 34.7900,
        "size": "enterprise",
        "work_style": "hybrid",
        "tech_stack": ["C++", "Network Security", "Python", "Linux", "Cybersecurity"],
        "open_positions": 8,
        "urgency_score": 78,
        "willing_station_b": True,
        "placement_fee_paid": False,
    },
]

# ── שיבוצים דמו ──────────────────────────────────────────────────
PLACEMENTS = [
    {
        "id": "PL_DEMO_001",
        "candidate_id": "CAND_YOAV_COHEN",
        "candidate_name": "יואב כהן",
        "school_id": "SCH_AMAL_TLV",
        "school_name": "תיכון עמל א' תל אביב",
        "company_id": "CO_CHECKPOINT_IL",
        "company_name": "Check Point Technologies",
        "score_a": 79,
        "score_b": 88,
        "final_score": 83.5,
        "status": "active",
        "created_at": "2026-06-01T10:00:00",
    },
    {
        "id": "PL_DEMO_002",
        "candidate_id": "CAND_MICHAL_LEVI",
        "candidate_name": "מיכל לוי",
        "school_id": "SCH_KATZIR_NAHARIYA",
        "school_name": "תיכון קציר נהריה",
        "company_id": "CO_MICROSOFT_IL",
        "company_name": "Microsoft Israel",
        "score_a": 84,
        "score_b": 71,
        "final_score": 77.5,
        "status": "active",
        "created_at": "2026-06-03T14:00:00",
    },
    {
        "id": "PL_DEMO_003",
        "candidate_id": "CAND_ROI_AVIV",
        "candidate_name": "רועי אביב",
        "school_id": "SCH_WEIZMANN_RISHON",
        "school_name": "תיכון ויצמן ראשון לציון",
        "company_id": "CO_MICROSOFT_IL",
        "company_name": "Microsoft Israel",
        "score_a": 72,
        "score_b": 84,
        "final_score": 78.0,
        "status": "pending",
        "created_at": "2026-06-07T09:00:00",
    },
]


def post(endpoint, data, label):
    try:
        r = requests.post(f"{BASE}/{endpoint}", json=data, timeout=20)
        if r.status_code in (200, 201):
            print(f"  OK{label}")
        else:
            print(f"  ERR{label} → {r.status_code}: {r.text[:120]}")
    except Exception as e:
        print(f"  FAIL{label} → {e}")


print("\n--- מועמדים ---")
for c in CANDIDATES:
    post("candidates", c, c["name"])

print("\n--- בתי ספר ---")
for s in SCHOOLS:
    post("schools", s, s["name"])

print("\n--- חברות ---")
for co in COMPANIES:
    post("companies", co, co["name"])

print("\n--- שיבוצים ---")
for p in PLACEMENTS:
    post("placements", p, f"{p['candidate_name']} → {p['school_name']}")

print("\n--- סטטיסטיקות ---")
try:
    r = requests.get(f"{BASE}/stats", timeout=15)
    print(json.dumps(r.json(), ensure_ascii=False, indent=2))
except Exception as e:
    print(f"  שגיאה: {e}")

print("\nSeed complete!")
