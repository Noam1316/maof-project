"""
Maof -- Scenario-Based Genetic Demo
=====================================
8 real personas x 4 schools x 3 companies.
Shows how the GA shifts weights to better predict placement success.

Usage:
  python demo_scenarios.py
"""

import sys, os, time
from typing import Dict
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))

from models.candidate import Candidate, AcademicBackground, MilitaryRole
from models.school import School
from models.company import Company
from genetic.optimizer import (
    run_genetic_optimizer, default_chromosome, Chromosome,
    compute_score_a_weighted, compute_score_b_weighted,
)
from scoring.score_c import calculate_score_c
from scoring.volume import calculate_volume_score
from matching.hungarian import run_hungarian, run_hungarian_with_capacity


# ─── SCENARIOS ───────────────────────────────────────────────────────────────

CANDIDATES = [
    Candidate(
        id="C001", name="יונתן — המורה הטבעי",
        eli5_score=92, subject="פיזיקה", additional_subjects=["מתמטיקה"],
        distance_km=5, family_status_score=90, commitment_score=95,
        career_switches=1, willing_periphery=False,
        tech_test_score=45, academic_background=AcademicBackground.BAGRUT_MATH,
        independent_courses=1, promotion_rate=60, military_role=MilitaryRole.MENTOR,
        team_size=4, conflict_resolution_score=80,
        preferred_company_size="mid", work_style="agile",
        preferred_location="תל אביב", willing_relocate=False,
        tech_stack=["Python"], years_experience=1,
    ),
    Candidate(
        id="C002", name="אביב — הסייברניסט",
        eli5_score=35, subject="סייבר", additional_subjects=[],
        distance_km=15, family_status_score=70, commitment_score=65,
        career_switches=2, willing_periphery=False,
        tech_test_score=95, academic_background=AcademicBackground.TECH_UNIT,
        independent_courses=4, promotion_rate=90, military_role=MilitaryRole.TECH_LEAD,
        team_size=8, conflict_resolution_score=70,
        preferred_company_size="startup", work_style="agile",
        preferred_location="תל אביב", willing_relocate=False,
        tech_stack=["Python", "C++", "TypeScript"], years_experience=3,
    ),
    Candidate(
        id="C003", name="מיכל — המאוזנת",
        eli5_score=70, subject="פייתון", additional_subjects=["מדעי מחשב"],
        distance_km=20, family_status_score=75, commitment_score=80,
        career_switches=1, willing_periphery=False,
        tech_test_score=72, academic_background=AcademicBackground.WARRIORS_TECH,
        independent_courses=3, promotion_rate=70, military_role=MilitaryRole.MENTOR,
        team_size=6, conflict_resolution_score=75,
        preferred_company_size="mid", work_style="agile",
        preferred_location="תל אביב", willing_relocate=True,
        tech_stack=["Python", "React"], years_experience=2,
    ),
    Candidate(
        id="C004", name="דניאל — הכוכב",
        eli5_score=88, subject="מתמטיקה", additional_subjects=["פיזיקה", "מדעי מחשב"],
        distance_km=8, family_status_score=85, commitment_score=90,
        career_switches=0, willing_periphery=True,
        tech_test_score=85, academic_background=AcademicBackground.ATUDA,
        independent_courses=5, promotion_rate=95, military_role=MilitaryRole.UNIT_COMMANDER,
        team_size=20, conflict_resolution_score=90,
        preferred_company_size="enterprise", work_style="hybrid",
        preferred_location="תל אביב", willing_relocate=True,
        tech_stack=["Python", "Java", "TypeScript"], years_experience=4,
    ),
    Candidate(
        id="C005", name="נועה — מוכנה לפריפריה",
        eli5_score=75, subject="מדעי מחשב", additional_subjects=["פייתון"],
        distance_km=65, family_status_score=80, commitment_score=85,
        career_switches=1, willing_periphery=True,
        tech_test_score=68, academic_background=AcademicBackground.PARTIAL_DEGREE,
        independent_courses=2, promotion_rate=65, military_role=MilitaryRole.MENTOR,
        team_size=5, conflict_resolution_score=78,
        preferred_company_size="mid", work_style="hybrid",
        preferred_location="באר שבע", willing_relocate=True,
        tech_stack=["Python", "JavaScript"], years_experience=2,
    ),
    Candidate(
        id="C006", name="עידן — הגבולי",
        eli5_score=63, subject="מתמטיקה", additional_subjects=[],
        distance_km=40, family_status_score=60, commitment_score=65,
        career_switches=3, willing_periphery=False,
        tech_test_score=62, academic_background=AcademicBackground.BAGRUT_MATH_CS,
        independent_courses=1, promotion_rate=55, military_role=MilitaryRole.SOLDIER,
        team_size=2, conflict_resolution_score=60,
        preferred_company_size="startup", work_style="agile",
        preferred_location="חיפה", willing_relocate=False,
        tech_stack=["Python"], years_experience=1,
    ),
    Candidate(
        id="C007", name="שירה — המפקדת",
        eli5_score=78, subject="סייבר", additional_subjects=["מדעי מחשב"],
        distance_km=12, family_status_score=85, commitment_score=88,
        career_switches=1, willing_periphery=False,
        tech_test_score=65, academic_background=AcademicBackground.TECH_UNIT,
        independent_courses=3, promotion_rate=85, military_role=MilitaryRole.UNIT_COMMANDER,
        team_size=15, conflict_resolution_score=92,
        preferred_company_size="enterprise", work_style="hybrid",
        preferred_location="תל אביב", willing_relocate=False,
        tech_stack=["Python", "C++"], years_experience=3,
    ),
    Candidate(
        id="C008", name="אור — עתודאי",
        eli5_score=72, subject="מדעי מחשב", additional_subjects=["פייתון", "מתמטיקה"],
        distance_km=25, family_status_score=78, commitment_score=82,
        career_switches=0, willing_periphery=True,
        tech_test_score=78, academic_background=AcademicBackground.ATUDA,
        independent_courses=4, promotion_rate=80, military_role=MilitaryRole.TECH_LEAD,
        team_size=10, conflict_resolution_score=82,
        preferred_company_size="enterprise", work_style="agile",
        preferred_location="תל אביב", willing_relocate=True,
        tech_stack=["Python", "Java", "React"], years_experience=2,
    ),
]

SCHOOLS = [
    School(
        id="S001", name="אופקים — שדרות (פריפריה דחופה)",
        location="שדרות", lat=31.52, lng=34.59,
        required_subjects=["סייבר", "מדעי מחשב"],
        grade_levels=["י", "יא", "יב"],
        socioeconomic_rank=2, nurturing_index=2,
        months_without_teacher=8, budget_available=True,
        capacity=2,
    ),
    School(
        id="S002", name="הרצל — תל אביב (מרכז)",
        location="תל אביב", lat=32.07, lng=34.78,
        required_subjects=["מתמטיקה", "פיזיקה"],
        grade_levels=["ט", "י", "יא", "יב"],
        socioeconomic_rank=7, nurturing_index=8,
        months_without_teacher=1, budget_available=True,
        capacity=2,
    ),
    School(
        id="S003", name="כנרת — טבריה (פריפריה צפון)",
        location="טבריה", lat=32.80, lng=35.53,
        required_subjects=["פייתון", "מדעי מחשב"],
        grade_levels=["ז", "ח", "ט", "י"],
        socioeconomic_rank=4, nurturing_index=3,
        months_without_teacher=4, budget_available=True,
        capacity=2,
    ),
    School(
        id="S004", name="שמיר — מודיעין (פרוור)",
        location="מודיעין", lat=31.89, lng=35.01,
        required_subjects=["מתמטיקה", "מדעי מחשב"],
        grade_levels=["ז", "ח", "ט", "י", "יא", "יב"],
        socioeconomic_rank=8, nurturing_index=9,
        months_without_teacher=2, budget_available=True,
        capacity=2,
    ),
]

COMPANIES = [
    Company(
        id="CO1", name="Microsoft Israel",
        location="תל אביב", lat=32.07, lng=34.78,
        size="enterprise", work_style="agile",
        tech_stack=["Python", "TypeScript", "Java", "React"],
        open_positions=5, urgency_score=80,
        willing_station_b=True, placement_fee_paid=False,
    ),
    Company(
        id="CO2", name="CyberArk",
        location="פתח תקווה", lat=32.09, lng=34.89,
        size="mid", work_style="hybrid",
        tech_stack=["Python", "C++", "TypeScript"],
        open_positions=3, urgency_score=70,
        willing_station_b=True, placement_fee_paid=False,
    ),
    Company(
        id="CO3", name="Startup X — AI Security",
        location="תל אביב", lat=32.07, lng=34.78,
        size="startup", work_style="agile",
        tech_stack=["Python", "React", "Node.js"],
        open_positions=2, urgency_score=60,
        willing_station_b=True, placement_fee_paid=False,
    ),
]


# ─── HELPERS ─────────────────────────────────────────────────────────────────

SEP  = "=" * 70
sep  = "-" * 70

def bar(v: float, width: int = 16) -> str:
    filled = int(max(0.0, min(100.0, v)) / 100.0 * width)
    return "[" + "#" * filled + "." * (width - filled) + "]"

def sign(d: float) -> str:
    return "^" if d > 0.02 else ("v" if d < -0.02 else "~")

def score_with(cand, school, company, w: Chromosome):
    a = compute_score_a_weighted(cand, school, w)
    b = compute_score_b_weighted(cand, company, w)
    c = calculate_score_c(a, b, cand, school, company)
    vol = calculate_volume_score(a, b, c)
    return a, b, c, vol["final_score"], vol["passes_threshold"]

def best_placement(cand, w: Chromosome):
    best_f, best_s, best_co = -1.0, SCHOOLS[0], COMPANIES[0]
    best_a, best_b, best_c, best_pass = 0.0, 0.0, 0.0, False
    for s in SCHOOLS:
        for co in COMPANIES:
            a, b, c, f, passes = score_with(cand, s, co, w)
            if f > best_f:
                best_f, best_s, best_co = f, s, co
                best_a, best_b, best_c, best_pass = a, b, c, passes
    return best_s, best_co, best_a, best_b, best_c, best_f, best_pass


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    print()
    print(SEP)
    print("  MAOF -- Scenario-Based Genetic Demo")
    print("  8 personas  x  4 schools  x  3 companies")
    print(SEP)

    # ── Personas ─────────────────────────────────────────────────────────────
    print()
    print("  CANDIDATES")
    print(sep)
    print(f"  {'ID':<5} {'Name':<28} {'ELI5':>5} {'Tech':>5} {'Subject':<16} {'Peri?'}")
    print(sep)
    for c in CANDIDATES:
        peri = "Yes" if c.willing_periphery else "No"
        print(f"  {c.id:<5} {c.name:<28} {c.eli5_score:>5.0f} {c.tech_test_score:>5.0f} {c.subject:<16} {peri}")

    print()
    print("  SCHOOLS")
    print(sep)
    print(f"  {'ID':<5} {'Name':<38} {'Rank':>5} {'Empty':>6}  Subjects")
    print(sep)
    for s in SCHOOLS:
        print(f"  {s.id:<5} {s.name:<38} {s.socioeconomic_rank:>5} {s.months_without_teacher:>5}m  {', '.join(s.required_subjects)}")

    print()
    print("  COMPANIES")
    print(sep)
    for co in COMPANIES:
        print(f"  {co.id:<5} {co.name:<28} {co.size:<12} urgency={co.urgency_score:.0f}  stack={co.tech_stack[:2]}")

    # ── Default weights ───────────────────────────────────────────────────────
    dw = default_chromosome()

    print()
    print(SEP)
    print("  STEP 1 — DEFAULT WEIGHTS (from spec)")
    print(SEP)
    print(f"  Score A:  ELI5={dw.w_eli5:.2f}  Subject={dw.w_subject:.2f}  Retention={dw.w_retention:.2f}  Impact={dw.w_impact:.2f}")
    print(f"  Score B:  Tech={dw.w_tech:.2f}   Growth={dw.w_growth:.2f}   Soft={dw.w_soft:.2f}      Culture={dw.w_culture:.2f}")
    print()
    print(f"  {'ID':<5} {'Name':<28} {'School':<7} {'Co':<5} {'A':>5} {'B':>5} {'C':>5} {'F':>6} {'Pass'}")
    print(sep)

    default_results = []
    for cand in CANDIDATES:
        s, co, a, b, c, f, passes = best_placement(cand, dw)
        icon = "V" if passes else "X"
        print(f"  {cand.id:<5} {cand.name:<28} {s.id:<7} {co.id:<5} {a:>5.1f} {b:>5.1f} {c:>5.1f} {f:>6.1f} {icon}")
        default_results.append((cand, s, co, a, b, c, f, passes))

    n_placed_def = sum(1 for r in default_results if r[7])
    total_val_def = sum(r[6] for r in default_results if r[7])
    print(sep)
    print(f"  Placed: {n_placed_def}/{len(CANDIDATES)}   Total value: {total_val_def:.1f}")

    # ── Run GA ───────────────────────────────────────────────────────────────
    print()
    print(SEP)
    print("  STEP 2 — GENETIC ALGORITHM (20 chromosomes x 30 generations)")
    print(SEP)
    t0 = time.time()
    result = run_genetic_optimizer(
        CANDIDATES, SCHOOLS, COMPANIES,
        population_size=20, generations=30, verbose=True,
    )
    elapsed = time.time() - t0
    print(f"\n  Completed in {elapsed:.1f}s")

    bw_data = result["best_weights"]
    bw = Chromosome(
        w_eli5      = bw_data["score_a"]["eli5"],
        w_subject   = bw_data["score_a"]["subject"],
        w_retention = bw_data["score_a"]["retention"],
        w_impact    = bw_data["score_a"]["impact"],
        w_tech      = bw_data["score_b"]["tech"],
        w_growth    = bw_data["score_b"]["growth"],
        w_soft      = bw_data["score_b"]["soft"],
        w_culture   = bw_data["score_b"]["culture"],
        fitness     = bw_data["fitness"],
    )

    # ── Weight shifts ─────────────────────────────────────────────────────────
    print()
    print(SEP)
    print("  STEP 3 — WEIGHT SHIFTS")
    print(SEP)
    shifts = [
        ("Score A  ELI5",      dw.w_eli5,      bw.w_eli5),
        ("Score A  Subject",   dw.w_subject,   bw.w_subject),
        ("Score A  Retention", dw.w_retention, bw.w_retention),
        ("Score A  Impact",    dw.w_impact,    bw.w_impact),
        ("Score B  Tech",      dw.w_tech,      bw.w_tech),
        ("Score B  Growth",    dw.w_growth,    bw.w_growth),
        ("Score B  Soft",      dw.w_soft,      bw.w_soft),
        ("Score B  Culture",   dw.w_culture,   bw.w_culture),
    ]
    for name, d_val, o_val in shifts:
        delta = o_val - d_val
        print(f"  {name:<22}  {d_val:.3f} --> {o_val:.3f}  {sign(delta)}  ({delta:+.3f})")

    df = result["default_weights"]["fitness"]
    bf = bw_data["fitness"]
    pct = ((bf - df) / df * 100) if df > 0 else 0
    print()
    print(f"  Fitness: {df:.4f} --> {bf:.4f}  ({pct:+.1f}%)")

    # ── Per-candidate before/after ────────────────────────────────────────────
    print()
    print(SEP)
    print("  STEP 4 — BEFORE vs AFTER: per candidate")
    print(SEP)
    print(f"  {'ID':<5} {'Name':<28} {'F-def':>6} {'F-opt':>6} {'Delta':>7}  Verdict")
    print(sep)

    n_placed_opt = 0
    total_val_opt = 0.0
    for (cand, _, _, _, _, _, def_f, def_pass) in default_results:
        _, _, opt_a, opt_b, opt_c, opt_f, opt_pass = best_placement(cand, bw)
        delta = opt_f - def_f

        if not def_pass and opt_pass:
            verdict = "NOW PASSES  <--"
        elif def_pass and not opt_pass:
            verdict = "DROPPED     (!)"
        elif delta > 3:
            verdict = "improved"
        elif delta < -3:
            verdict = "declined"
        else:
            verdict = "stable"

        if opt_pass:
            n_placed_opt += 1
            total_val_opt += opt_f

        arrow = "^" if delta > 0 else ("v" if delta < 0 else "~")
        print(f"  {cand.id:<5} {cand.name:<28} {def_f:>6.1f} {opt_f:>6.1f} {delta:>+7.1f}  {verdict}")

    print(sep)
    print(f"  Placed: {n_placed_opt}/{len(CANDIDATES)} (was {n_placed_def})   "
          f"Total value: {total_val_opt:.1f} (was {total_val_def:.1f})")

    # ── Learning curve ────────────────────────────────────────────────────────
    print()
    print(SEP)
    print("  LEARNING CURVE")
    print(SEP)
    for entry in result["history"]:
        if entry["generation"] % 5 == 0 or entry["generation"] == 1:
            b = entry["best_fitness"]
            a = entry["avg_fitness"]
            print(f"  gen {entry['generation']:>3}  best={b:.4f} {bar(b)}  avg={a:.4f}")

    # ── Capacity-Aware Hungarian ──────────────────────────────────────────────
    print()
    print(SEP)
    print("  STEP 5 — CAPACITY-AWARE HUNGARIAN")
    print(f"  Schools: each capacity=2  |  Companies: CO1={COMPANIES[0].open_positions} CO2={COMPANIES[1].open_positions} CO3={COMPANIES[2].open_positions}")
    print(SEP)

    # בנה score_3d[candidate][school][company] עם המשקלות האופטימליות
    score_3d = []
    for cand in CANDIDATES:
        row_s = []
        for school in SCHOOLS:
            row_c = []
            for company in COMPANIES:
                a = compute_score_a_weighted(cand, school, bw)
                b = compute_score_b_weighted(cand, company, bw)
                c = calculate_score_c(a, b, cand, school, company)
                vol = calculate_volume_score(a, b, c)
                row_c.append(vol["final_score"])
            row_s.append(row_c)
        score_3d.append(row_s)

    cand_ids = [c.id for c in CANDIDATES]

    # שיבוץ קלאסי (ללא קיבולות) — Hungarian על כל הזוגות ישר
    classic_placements = [f"{s.id}__{c.id}" for s in SCHOOLS for c in COMPANIES]
    classic_scores = [
        [score_3d[ci][si][ki] for si in range(len(SCHOOLS)) for ki in range(len(COMPANIES))]
        for ci in range(len(CANDIDATES))
    ]
    classic_result = run_hungarian(cand_ids, classic_placements, classic_scores)

    # שיבוץ עם קיבולות
    cap_result = run_hungarian_with_capacity(cand_ids, SCHOOLS, COMPANIES, score_3d)

    # ספור כמה מועמדים שובצו לכל בי"ס ב-classic
    school_counts_classic: Dict[str, int] = {}
    for r in classic_result:
        pid = r["placement_id"]
        s_id = pid.split("__")[0]
        school_counts_classic[s_id] = school_counts_classic.get(s_id, 0) + 1
    violations = {s: n for s, n in school_counts_classic.items() if n > 2}  # cap=2

    classic_placed = len(classic_result)
    classic_val    = sum(r["final_score"] for r in classic_result)
    cap_placed     = len(cap_result)
    cap_val        = sum(r["final_score"] for r in cap_result)
    unplaced_ids   = sorted(set(cand_ids) - {r["candidate_id"] for r in cap_result})

    print(f"  {'Method':<24} {'Placed':>6}  {'Value':>8}  Notes")
    print("  " + "-" * 62)
    viol_str = f"  ⚠ {', '.join(f'{s}×{n}' for s,n in violations.items())} עוברים cap=2" if violations else "  ✓ (אין בדיקת קיבולת)"
    print(f"  {'Classic (ללא קיבולות)':<24} {classic_placed:>6}  {classic_val:>8.1f}{viol_str}")
    print(f"  {'Capacity-aware':<24} {cap_placed:>6}  {cap_val:>8.1f}  ✓ כל הגבולות מכובדים")

    if violations:
        print()
        print("  הערה: Classic 'משבץ' יותר מועמדים כי מתעלם מקיבולת.")
        print("  Capacity-aware נותן את התוצאה הנכונה לעולם האמיתי.")

    if unplaced_ids:
        print()
        print(f"  לא שובצו (אין בי\"ס זמין בתחום שלהם): {', '.join(unplaced_ids)}")

    print()
    print(f"  {'ID':<5} {'Name':<28} {'School':<7} {'Company':<22} {'Score':>6}")
    print("  " + "-" * 70)
    for r in cap_result:
        cand_name = next(c.name for c in CANDIDATES if c.id == r["candidate_id"])
        co_name   = next(c.name for c in COMPANIES   if c.id == r["company_id"])
        print(f"  {r['candidate_id']:<5} {cand_name:<28} {r['school_id']:<7} {co_name:<22} {r['final_score']:>6.1f}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print(SEP)
    print("  SUMMARY")
    print(SEP)
    print(f"  Dataset        : {len(CANDIDATES)} candidates | {len(SCHOOLS)} schools (cap=2) | {len(COMPANIES)} companies")
    print(f"  Fitness gain   : {df:.4f} --> {bf:.4f}  ({pct:+.1f}%)")
    print(f"  Placed (GA)    : {n_placed_def} --> {n_placed_opt}  (delta: {n_placed_opt - n_placed_def:+d})")
    print(f"  Total value    : {total_val_def:.1f} --> {total_val_opt:.1f}  ({total_val_opt - total_val_def:+.1f})")
    print(f"  Capacity match : {cap_placed}/{len(CANDIDATES)} placed  (value={cap_val:.1f})")
    print()
    print("  Persisting weights to weights.json...")
    from feedback.weight_store import save_weights, load_weights, get_weight_info
    weights = load_weights()
    weights["score_a"] = bw_data["score_a"]
    weights["score_b"] = bw_data["score_b"]
    save_weights(weights, source="genetic_algorithm")
    info = get_weight_info()
    print(f"  Saved  source={info['source']}  updated={info['updated_at'][:19]}")
    print(f"  Score A: {info['score_a']}")
    print(f"  Score B: {info['score_b']}")
    print(SEP)
    print()


if __name__ == "__main__":
    main()
