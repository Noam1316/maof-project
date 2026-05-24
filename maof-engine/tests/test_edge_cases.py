"""
Tests — Edge Cases & Boundary Values
מעוף Tech-Lead Israel

מכסה:
  - ערכי גבול (0, 60, 100) בסקורינג
  - Score C: שלבי נכונות, דחיפות, קרבה
  - Volume: threshold בדיוק 60, ערכים קיצוניים
  - Hungarian: יותר מועמדים ממשרות ולהיפך
  - Feedback Loop: חישוב שגיאה, ניתוח, export
  - Genetic Algorithm: נורמליזציה, כרומוזום
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scoring.volume import calculate_volume_score, MIN_THRESHOLD
from scoring.score_a import calculate_score_a, distance_score, retention_score, impact_score
from scoring.score_b import calculate_score_b, cultural_fit_score, SIZE_PROXIMITY
from scoring.score_c import calculate_score_c, urgency_score, willingness_score
from matching.hungarian import run_hungarian
from models.candidate import Candidate, AcademicBackground, MilitaryRole
from models.school import School
from models.company import Company
from genetic.optimizer import (
    normalize_4, random_chromosome, default_chromosome,
    crossover, mutate, Chromosome,
)
from feedback.loop import (
    SchoolFeedback, CompanyFeedback, CandidateFeedback,
    PlacementRecord, _clamp,
)


# ─── Fixtures ────────────────────────────────────────────────

def make_candidate(**kwargs) -> Candidate:
    defaults = dict(
        id="C001", name="Test",
        eli5_score=80.0, subject="סייבר", additional_subjects=["פייתון"],
        distance_km=10.0, family_status_score=80.0, commitment_score=90.0,
        career_switches=1, willing_periphery=False,
        tech_test_score=85.0, academic_background=AcademicBackground.TECH_UNIT,
        independent_courses=3, promotion_rate=80.0,
        military_role=MilitaryRole.TECH_LEAD, team_size=8,
        conflict_resolution_score=75.0, preferred_company_size="mid",
        work_style="agile", preferred_location="תל אביב",
        willing_relocate=False, tech_stack=["Python", "React"],
        years_experience=2.0,
    )
    defaults.update(kwargs)
    return Candidate(**defaults)


def make_school(**kwargs) -> School:
    defaults = dict(
        id="S001", name="בית ספר", location="תל אביב",
        lat=32.0, lng=34.8, required_subjects=["סייבר", "פייתון"],
        grade_levels=["ט", "י"], socioeconomic_rank=3,
        nurturing_index=4, months_without_teacher=6, budget_available=True,
    )
    defaults.update(kwargs)
    return School(**defaults)


def make_company(**kwargs) -> Company:
    defaults = dict(
        id="CO001", name="חברה", location="תל אביב",
        lat=32.0, lng=34.8, size="mid", work_style="agile",
        tech_stack=["Python", "React", "Node.js"],
        open_positions=2, urgency_score=70.0,
        willing_station_b=True, placement_fee_paid=False,
    )
    defaults.update(kwargs)
    return Company(**defaults)


# ═══════════════════════════════════════════════════════════════
# VOLUME — BOUNDARY VALUES
# ═══════════════════════════════════════════════════════════════

def test_volume_exactly_at_threshold():
    """60 בדיוק — צריך לעבור (>=60, לא >60)"""
    result = calculate_volume_score(60.0, 60.0, 60.0)
    assert result["passes_threshold"] is True
    assert result["volume_score"] == 0.0  # (0*0*0)^(1/3) = 0
    assert result["final_score"] >= 0


def test_volume_just_below_threshold():
    """59.99 — לא עובר"""
    result = calculate_volume_score(59.99, 100.0, 100.0)
    assert result["passes_threshold"] is False
    assert result["final_score"] == 0.0


def test_volume_all_perfect():
    """100 בכל ציון — ציון מקסימלי"""
    result = calculate_volume_score(100, 100, 100)
    assert result["passes_threshold"] is True
    assert result["volume_score"] > 90
    assert result["final_score"] > 90


def test_volume_asymmetric_high_low():
    """95+95+61 — עובר אבל ציון נמוך בגלל C"""
    result = calculate_volume_score(95, 95, 61)
    assert result["passes_threshold"] is True
    low_vol = result["volume_score"]

    result2 = calculate_volume_score(95, 95, 95)
    high_vol = result2["volume_score"]

    assert high_vol > low_vol * 2  # הבדל משמעותי


def test_volume_score_never_exceeds_100():
    """ציון סופי לא עולה על 100"""
    result = calculate_volume_score(100, 100, 100)
    assert result["volume_score"] <= 100
    assert result["final_score"] <= 100


def test_volume_score_never_negative():
    """ציון לא שלילי"""
    result = calculate_volume_score(60, 60, 60)
    assert result["volume_score"] >= 0
    assert result["final_score"] >= 0


def test_volume_zero_scores():
    """0 בכל ציון — לא עובר"""
    result = calculate_volume_score(0, 0, 0)
    assert result["passes_threshold"] is False


def test_volume_breakdown_contains_all_scores():
    """breakdown מכיל A, B, C"""
    result = calculate_volume_score(80, 80, 80)
    bd = result["breakdown"]
    assert "score_a" in bd
    assert "score_b" in bd
    assert "score_c" in bd


# ═══════════════════════════════════════════════════════════════
# DISTANCE — EDGE CASES
# ═══════════════════════════════════════════════════════════════

def test_distance_zero():
    """מרחק 0 — ציון מקסימלי"""
    assert distance_score(0, False) == 100.0


def test_distance_exactly_10():
    """10 ק"מ — גבול עליון של הטווח"""
    assert distance_score(10, False) == 100.0


def test_distance_exactly_25():
    assert distance_score(25, False) == 80.0


def test_distance_exactly_40():
    assert distance_score(40, False) == 60.0


def test_distance_exactly_60():
    assert distance_score(60, False) == 35.0


def test_distance_very_large():
    """מרחק 1000 ק"מ — ציון מינימלי"""
    assert distance_score(1000, False) == 10.0


def test_distance_periphery_overrides_all():
    """willing_periphery=True מבטל כל קנס מרחק"""
    for km in [0, 50, 100, 500]:
        assert distance_score(km, True) == 100.0


# ═══════════════════════════════════════════════════════════════
# SCORE A — EDGE CASES
# ═══════════════════════════════════════════════════════════════

def test_score_a_zero_eli5():
    """ELI5=0 — ציון נמוך אבל לא 0 (יש רכיבים אחרים)"""
    c = make_candidate(eli5_score=0.0)
    s = make_school()
    score = calculate_score_a(c, s)
    assert 0 < score < 100


def test_score_a_perfect_eli5():
    """ELI5=100 — ציון A גבוה"""
    c = make_candidate(eli5_score=100.0)
    s = make_school()
    score = calculate_score_a(c, s)
    assert score > 60


def test_score_a_no_additional_subjects():
    """אין מקצועות נוספים"""
    c = make_candidate(additional_subjects=[])
    s = make_school()
    score = calculate_score_a(c, s)
    assert 0 <= score <= 100


def test_score_a_many_career_switches():
    """הרבה החלפות קריירה — פוגע בשימור"""
    c_stable = make_candidate(career_switches=0)
    c_unstable = make_candidate(career_switches=10)
    s = make_school()

    score_stable = calculate_score_a(c_stable, s)
    score_unstable = calculate_score_a(c_unstable, s)

    assert score_stable > score_unstable


def test_impact_periphery_school():
    """בית ספר בפריפריה (דירוג 1) = impact גבוה"""
    peripheral = make_school(socioeconomic_rank=1, nurturing_index=1, months_without_teacher=12)
    rich = make_school(socioeconomic_rank=10, nurturing_index=10, months_without_teacher=0)

    assert impact_score(peripheral) > impact_score(rich)


# ═══════════════════════════════════════════════════════════════
# SCORE B — EDGE CASES
# ═══════════════════════════════════════════════════════════════

def test_score_b_no_tech_stack():
    """מועמד ללא tech stack"""
    c = make_candidate(tech_stack=[])
    co = make_company()
    score = calculate_score_b(c, co)
    assert 0 <= score <= 100


def test_score_b_company_no_stack():
    """חברה ללא stack — ברירת מחדל 80"""
    c = make_candidate()
    co = make_company(tech_stack=[])
    score = calculate_score_b(c, co)
    assert score > 0


def test_score_b_all_academic_backgrounds():
    """כל סוגי רקע אקדמי — לא קורס"""
    co = make_company()
    for bg in AcademicBackground:
        c = make_candidate(academic_background=bg)
        score = calculate_score_b(c, co)
        assert 0 <= score <= 100, f"Failed for {bg}"


def test_score_b_all_military_roles():
    """כל תפקידים צבאיים — לא קורס"""
    co = make_company()
    for role in MilitaryRole:
        c = make_candidate(military_role=role)
        score = calculate_score_b(c, co)
        assert 0 <= score <= 100, f"Failed for {role}"


def test_cultural_fit_all_size_combos():
    """כל שילובי גודל חברה — ציון תקין"""
    sizes = ["startup", "mid", "enterprise"]
    for c_size in sizes:
        for co_size in sizes:
            c = make_candidate(preferred_company_size=c_size)
            co = make_company(size=co_size)
            score = cultural_fit_score(c, co)
            assert 0 <= score <= 100, f"Failed for {c_size}→{co_size}"


def test_cultural_fit_same_size_is_best():
    """גודל זהה = ציון הכי גבוה"""
    for size in ["startup", "mid", "enterprise"]:
        c = make_candidate(preferred_company_size=size, work_style="agile", preferred_location="תל אביב")
        co = make_company(size=size, work_style="agile", location="תל אביב")
        score = cultural_fit_score(c, co)
        assert score == 100.0


def test_cultural_fit_unknown_size():
    """גודל לא מוכר — fallback ל-50"""
    c = make_candidate(preferred_company_size="micro")
    co = make_company(size="giant")
    score = cultural_fit_score(c, co)
    assert 0 <= score <= 100


# ═══════════════════════════════════════════════════════════════
# SCORE C — THREE-WAY SCORE
# ═══════════════════════════════════════════════════════════════

def test_urgency_both_urgent():
    s = make_school(months_without_teacher=6)
    co = make_company(urgency_score=80)
    assert urgency_score(s, co) == 100.0


def test_urgency_neither_urgent():
    s = make_school(months_without_teacher=1)
    co = make_company(urgency_score=30)
    assert urgency_score(s, co) == 30.0


def test_urgency_only_school():
    s = make_school(months_without_teacher=6)
    co = make_company(urgency_score=30)
    assert urgency_score(s, co) == 60.0


def test_willingness_phase_1():
    """שלב 1 (<50 שיבוצים) — רק מועמד חשוב"""
    assert willingness_score(True, False, False, 10) == 100.0
    assert willingness_score(False, True, True, 10) == 0.0


def test_willingness_phase_2():
    """שלב 2 (50-199) — מועמד + חברה"""
    assert willingness_score(True, True, False, 100) == 100.0
    assert willingness_score(True, False, False, 100) == 50.0
    assert willingness_score(False, False, False, 100) == 0.0


def test_willingness_phase_3():
    """שלב 3 (200+) — כולם"""
    assert willingness_score(True, True, True, 300) == 100.0
    assert willingness_score(True, True, False, 300) == 67.0
    assert willingness_score(False, False, False, 300) == 0.0


def test_score_c_range():
    c = make_candidate()
    s = make_school()
    co = make_company()
    score = calculate_score_c(80, 80, c, s, co, 0)
    assert 0 <= score <= 100


def test_score_c_symmetric_ab():
    """min(A,B) זהה בשני הכיוונים"""
    c = make_candidate()
    s = make_school()
    co = make_company()
    c1 = calculate_score_c(90, 60, c, s, co)
    c2 = calculate_score_c(60, 90, c, s, co)
    assert abs(c1 - c2) < 1.0


# ═══════════════════════════════════════════════════════════════
# HUNGARIAN — EDGE CASES
# ═══════════════════════════════════════════════════════════════

def test_hungarian_more_candidates_than_positions():
    """5 מועמדים, 3 משרות — רק 3 משובצים"""
    candidates = ["C1", "C2", "C3", "C4", "C5"]
    placements = ["P1", "P2", "P3"]
    scores = [
        [90, 50, 30],
        [40, 85, 20],
        [10, 30, 75],
        [60, 60, 60],
        [70, 40, 50],
    ]
    results = run_hungarian(candidates, placements, scores)
    assert len(results) <= 3


def test_hungarian_more_positions_than_candidates():
    """2 מועמדים, 5 משרות"""
    candidates = ["C1", "C2"]
    placements = ["P1", "P2", "P3", "P4", "P5"]
    scores = [
        [90, 50, 30, 70, 80],
        [40, 85, 20, 60, 50],
    ]
    results = run_hungarian(candidates, placements, scores)
    assert len(results) <= 2


def test_hungarian_single_candidate():
    """מועמד יחיד — 1 שיבוץ"""
    results = run_hungarian(["C1"], ["P1"], [[95]])
    assert len(results) == 1
    assert results[0]["final_score"] == 95


def test_hungarian_all_zeros():
    """כל הציונים 0 — אין שיבוצים"""
    results = run_hungarian(["C1", "C2"], ["P1", "P2"], [[0, 0], [0, 0]])
    for r in results:
        assert r["final_score"] == 0


def test_hungarian_diagonal_optimal():
    """מטריצה אלכסונית — שיבוץ ברור"""
    results = run_hungarian(
        ["C1", "C2", "C3"],
        ["P1", "P2", "P3"],
        [[100, 0, 0], [0, 100, 0], [0, 0, 100]],
    )
    assert len(results) == 3
    total = sum(r["final_score"] for r in results)
    assert total == 300


# ═══════════════════════════════════════════════════════════════
# GENETIC ALGORITHM
# ═══════════════════════════════════════════════════════════════

def test_normalize_4_sums_to_1():
    a, b, c, d = normalize_4(10, 20, 30, 40)
    assert abs((a + b + c + d) - 1.0) < 0.001


def test_normalize_4_all_zeros():
    """כולם 0 → חלוקה שווה"""
    a, b, c, d = normalize_4(0, 0, 0, 0)
    assert a == b == c == d == 0.25


def test_random_chromosome_valid():
    c = random_chromosome()
    sum_a = c.w_eli5 + c.w_subject + c.w_retention + c.w_impact
    sum_b = c.w_tech + c.w_growth + c.w_soft + c.w_culture
    assert abs(sum_a - 1.0) < 0.001
    assert abs(sum_b - 1.0) < 0.001


def test_default_chromosome_values():
    c = default_chromosome()
    assert c.w_eli5 == 0.35
    assert c.w_tech == 0.35
    assert c.w_impact == 0.15
    assert c.w_culture == 0.15


def test_crossover_preserves_normalization():
    p1 = random_chromosome()
    p2 = random_chromosome()
    c1, c2 = crossover(p1, p2)

    for child in [c1, c2]:
        sum_a = child.w_eli5 + child.w_subject + child.w_retention + child.w_impact
        sum_b = child.w_tech + child.w_growth + child.w_soft + child.w_culture
        assert abs(sum_a - 1.0) < 0.001
        assert abs(sum_b - 1.0) < 0.001


def test_mutate_preserves_normalization():
    c = default_chromosome()
    mutated = mutate(c, mutation_rate=1.0)  # mutate all
    sum_a = mutated.w_eli5 + mutated.w_subject + mutated.w_retention + mutated.w_impact
    sum_b = mutated.w_tech + mutated.w_growth + mutated.w_soft + mutated.w_culture
    assert abs(sum_a - 1.0) < 0.001
    assert abs(sum_b - 1.0) < 0.001


# ═══════════════════════════════════════════════════════════════
# FEEDBACK LOOP — DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

def test_clamp_normal():
    assert _clamp(50) == 50


def test_clamp_below_zero():
    assert _clamp(-10) == 0.0


def test_clamp_above_100():
    assert _clamp(150) == 100.0


def test_school_feedback_actual_score():
    fb = SchoolFeedback(
        placement_id="P1", candidate_id="C1", school_id="S1", date="2026-01",
        teacher_rating=80, attendance_rate=90,
        principal_satisfaction=70, student_satisfaction=85,
    )
    score = fb.actual_score
    expected = 80 * 0.40 + 90 * 0.20 + 70 * 0.25 + 85 * 0.15
    assert abs(score - expected) < 0.01


def test_school_feedback_clamps_values():
    """ערכים מעל 100 — נחתכים"""
    fb = SchoolFeedback(
        placement_id="P1", candidate_id="C1", school_id="S1", date="",
        teacher_rating=150, attendance_rate=-10,
        principal_satisfaction=100, student_satisfaction=100,
    )
    assert fb.teacher_rating == 100.0
    assert fb.attendance_rate == 0.0


def test_company_feedback_actual_score():
    fb = CompanyFeedback(
        placement_id="P1", candidate_id="C1", company_id="CO1", date="",
        performance_score=90, progression_rate=80, manager_satisfaction=70,
    )
    expected = 90 * 0.50 + 80 * 0.30 + 70 * 0.20
    assert abs(fb.actual_score - expected) < 0.01


def test_candidate_feedback_actual_score():
    fb = CandidateFeedback(
        placement_id="P1", candidate_id="C1", date="",
        school_satisfaction=80, company_satisfaction=90, overall_satisfaction=85,
    )
    expected = 80 * 0.35 + 90 * 0.40 + 85 * 0.25
    assert abs(fb.actual_score - expected) < 0.01


def test_placement_record_no_feedback():
    """שיבוץ ללא משוב"""
    r = PlacementRecord(
        placement_id="P1", candidate_id="C1",
        school_id="S1", company_id="CO1",
        predicted_score=75.0,
    )
    assert r.actual_score is None
    assert r.prediction_error is None
    assert r.has_full_feedback is False


def test_placement_record_partial_feedback():
    """משוב חלקי — רק בית ספר"""
    r = PlacementRecord(
        placement_id="P1", candidate_id="C1",
        school_id="S1", company_id="CO1",
        predicted_score=75.0,
        school_feedback=SchoolFeedback(
            placement_id="P1", candidate_id="C1", school_id="S1", date="",
            teacher_rating=80, attendance_rate=90,
            principal_satisfaction=70, student_satisfaction=85,
        ),
    )
    assert r.actual_score is not None
    assert r.prediction_error is not None
    assert r.has_full_feedback is False


def test_placement_record_full_feedback():
    """משוב מלא"""
    r = PlacementRecord(
        placement_id="P1", candidate_id="C1",
        school_id="S1", company_id="CO1",
        predicted_score=75.0,
        school_feedback=SchoolFeedback("P1", "C1", "S1", "", 80, 90, 70, 85),
        company_feedback=CompanyFeedback("P1", "C1", "CO1", "", 85, 75, 80),
        candidate_feedback=CandidateFeedback("P1", "C1", "", 80, 90, 85),
    )
    assert r.has_full_feedback is True
    assert r.actual_score is not None
    assert 0 <= r.actual_score <= 100


def test_placement_record_prediction_error_sign():
    """predicted > actual → error חיובי"""
    fb = SchoolFeedback("P1", "C1", "S1", "", 50, 50, 50, 50)
    r = PlacementRecord("P1", "C1", "S1", "CO1", predicted_score=90.0, school_feedback=fb)
    assert r.prediction_error > 0  # 90 - ~50 = positive


def test_feedback_to_dict():
    """to_dict מחזיר את כל השדות"""
    fb = SchoolFeedback("P1", "C1", "S1", "2026-03", 80, 90, 70, 85)
    d = fb.to_dict()
    assert d["placement_id"] == "P1"
    assert d["teacher_rating"] == 80
    assert "actual_score" in d


# ═══════════════════════════════════════════════════════════════
# INTEGRATION — FULL PIPELINE EDGE CASES
# ═══════════════════════════════════════════════════════════════

def test_pipeline_single_candidate():
    """מועמד יחיד — עדיין עובד"""
    from main import run_full_matching
    from data.synthetic import generate_dataset

    candidates, schools, companies = generate_dataset(1, 1, 1)
    results = run_full_matching(candidates, schools, companies)
    assert "assignments" in results
    assert len(results["assignments"]) <= 1


def test_pipeline_many_candidates():
    """20 מועמדים — ביצועים סבירים"""
    from main import run_full_matching
    from data.synthetic import generate_dataset

    candidates, schools, companies = generate_dataset(20, 8, 8)
    results = run_full_matching(candidates, schools, companies)
    assert results["total_value"] >= 0
    assert len(results["assignments"]) <= 20


def test_synthetic_data_valid():
    """נתונים סינתטיים תקינים"""
    from data.synthetic import generate_dataset

    candidates, schools, companies = generate_dataset(10, 5, 5)
    assert len(candidates) == 10
    assert len(schools) == 5
    assert len(companies) == 5

    for c in candidates:
        assert 0 <= c.eli5_score <= 100
        assert 0 <= c.tech_test_score <= 100
        assert c.distance_km >= 0


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
