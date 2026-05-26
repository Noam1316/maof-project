"""
Demo Live — בדיקות מול API חי
https://maof-project.onrender.com

מריץ 6 בדיקות ומדפיס תוצאות מסודרות.
"""

import sys
import httpx

sys.stdout.reconfigure(encoding="utf-8")

BASE = "https://maof-project.onrender.com"

PASS = "✅"
FAIL = "❌"

def section(title):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")

def check(label, ok, detail=""):
    icon = PASS if ok else FAIL
    print(f"  {icon}  {label}")
    if detail:
        print(f"      {detail}")


# ─── 1. Health Check ─────────────────────────────────────────────
section("1. Health Check")
r = httpx.get(f"{BASE}/api/v1/health", timeout=60)
data = r.json()
check("Server alive", r.status_code == 200)
check("Engine name correct", "Maof" in data.get("engine", ""), data.get("engine"))


# ─── 2. סימולציה מהירה ───────────────────────────────────────────
section("2. סימולציה מהירה — 5 מועמדים, 3 בתי ספר, 3 חברות")
r = httpx.get(f"{BASE}/api/v1/simulate/quick", timeout=60)
data = r.json()
assignments = data.get("assignments", [])
stats = data.get("stats", {})

check("סטטוס 200", r.status_code == 200)
check(f"שיבוצים בוצעו: {len(assignments)}", len(assignments) > 0)
check(f"מועמדים: {stats.get('candidates')} | בתי ספר: {stats.get('schools')} | חברות: {stats.get('companies')}", True)
check(f"שיבוצים מוצלחים: {stats.get('successful_assignments')}/{stats.get('placements')}", True)

print("\n  TOP 3 שיבוצים:")
for a in assignments[:3]:
    print(f"    מועמד {a['candidate_id']} → {a['placement_id']} | ציון: {a['final_score']:.1f} | דירוג #{a['rank']}")


# ─── 3. ציון בודד ────────────────────────────────────────────────
section("3. ציון בודד — נועם (מח\"ט, סייבר, 8 ק\"מ)")
payload = {
    "candidate": {
        "id": "C_NOAM",
        "name": "נועם",
        "eli5_score": 82.0,
        "subject": "סייבר",
        "additional_subjects": ["פייתון", "נתונים"],
        "distance_km": 8.0,
        "family_status_score": 75.0,
        "commitment_score": 90.0,
        "career_switches": 0,
        "willing_periphery": True,
        "tech_test_score": 88.0,
        "academic_background": "warriors_tech",
        "independent_courses": 4,
        "military_role": "tech_lead",
        "team_size": 12,
        "conflict_resolution_score": 80.0,
        "promotion_rate": 85.0,
        "preferred_company_size": "medium",
        "preferred_location": "center",
        "work_style": "hybrid",
        "willing_relocate": True,
        "tech_stack": ["Python", "AI", "Data Science", "Cyber"]
    },
    "school": {
        "id": "S_SDEROT",
        "name": "תיכון שדרות",
        "location": "שדרות",
        "lat": 31.5,
        "lng": 34.6,
        "required_subjects": ["סייבר", "פייתון"],
        "grade_levels": ["י", "יא", "יב"],
        "socioeconomic_rank": 3,
        "nurturing_index": 8,
        "months_without_teacher": 8,
        "budget_available": True
    },
    "company": {
        "id": "CO_MSFT",
        "name": "Microsoft Israel",
        "location": "תל אביב",
        "lat": 32.08,
        "lng": 34.78,
        "size": "large",
        "work_style": "hybrid",
        "tech_stack": ["Python", "AI", "Cloud", "Cyber"],
        "open_positions": 3,
        "urgency_score": 85.0,
        "willing_station_b": True
    },
    "total_placements": 10
}

r = httpx.post(f"{BASE}/api/v1/score", json=payload, timeout=60)
data = r.json()

check("סטטוס 200", r.status_code == 200)
check(f"ציון A (הוראה):  {data.get('score_a', 0):.1f}/100", data.get('score_a', 0) >= 60,
      "כושר הוראה + התאמת מקצוע + שימור + impact")
check(f"ציון B (חברה):   {data.get('score_b', 0):.1f}/100", data.get('score_b', 0) >= 60,
      "מיומנות טכנית + צמיחה + soft skills + תרבות")
check(f"ציון סופי:       {data.get('final_score', 0):.1f}/100", data.get('final_score', 0) >= 60)
check(f"עובר סף:         {data.get('passes_threshold')}", data.get('passes_threshold') is True)


# ─── 4. ELI5 — הסבר טוב vs ז'רגון ───────────────────────────────
section("4. מבחן ELI5 — הסבר טוב מול ז'רגון")

good = "סייבר זה כמו מנעול על הדלת של המחשב שלך. דמיין שהמחשב הוא בית — אנשים רעים רוצים להיכנס. אנשי הסייבר הם השומרים. לדוגמה, סיסמה חזקה זה כמו מפתח שקשה לנחש."
bad  = "אבטחת מידע וסייבר עוסקת בהגנה על מערכות מחשוב ממתקפות זדוניות. פרוטוקולי אבטחה כוללים הצפנה, אימות דו-שלבי ובדיקת פגיעויות במערכות המידע הארגוניות."

r_good = httpx.post(f"{BASE}/api/v1/eli5", json={"text": good}, timeout=60)
r_bad  = httpx.post(f"{BASE}/api/v1/eli5", json={"text": bad},  timeout=60)

g = r_good.json()
b = r_bad.json()

check(f"הסבר טוב:  {g['total_score']:.0f}/100 (עובר: {g['passes_minimum']})",
      g['passes_minimum'] is True)
check(f"ז'רגון:    {b['total_score']:.0f}/100 (עובר: {b['passes_minimum']})",
      g['total_score'] > b['total_score'],
      f"הפרש: +{g['total_score'] - b['total_score']:.0f} לטובת ההסבר הטוב")

print("\n  פירוט הסבר טוב:")
for k, v in g['breakdown'].items():
    bar = "█" * int(v / 10) + "░" * (10 - int(v / 10))
    print(f"    {k:<12} {bar} {v:.0f}")


# ─── 5. ELI5 Compare — בונוס תמציתיות ───────────────────────────
section("5. ELI5 Compare — בונוס תמציתיות")
r = httpx.post(f"{BASE}/api/v1/eli5/compare",
               json={"text": good, "topic": "סייבר"}, timeout=60)
data = r.json()

check("סטטוס 200", r.status_code == 200)
check(f"ציון בסיס:    {data['base_score']:.1f}", True)
check(f"בונוס תמציתיות: +{data['conciseness_bonus']:.2f}", True,
      data['conciseness_analysis'].get('reason', ''))
check(f"ציון סופי:    {data['final_score']:.1f}/100", data['final_score'] >= 60)
check(f"Similarity:   {data['similarity']['score']} ({data['similarity']['method']})", True)


# ─── 6. סימולציה מלאה ────────────────────────────────────────────
section("6. סימולציה מלאה — 10 מועמדים, 5 בתי ספר, 5 חברות")
r = httpx.post(f"{BASE}/api/v1/simulate",
               json={"n_candidates": 10, "n_schools": 5, "n_companies": 5},
               timeout=60)
data = r.json()
stats = data["results"]["stats"]
assignments = data["results"]["assignments"]

check("סטטוס 200", r.status_code == 200)
check(f"שיבוצים: {stats['successful_assignments']}/{stats['placements']}", True)
check(f"ערך כולל: {data['results']['total_value']:.1f}", True)

scores = [a['final_score'] for a in assignments]
if scores:
    avg = sum(scores) / len(scores)
    check(f"ממוצע ציון שיבוצים: {avg:.1f}/100", avg >= 40)


# ─── סיכום ───────────────────────────────────────────────────────
section("סיכום")
print(f"""
  🌐 API:   {BASE}
  📖 Docs:  {BASE}/docs

  המנוע עובד — Hungarian Algorithm משבץ בזמן אמת,
  ELI5 מנתח יכולת הסבר, Feedback Loop מוכן לנתונים אמיתיים.
""")
