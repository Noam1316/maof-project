"""
Tests — Dual Scoring Engine
מעוף Tech-Lead Israel
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from scoring.volume import calculate_volume_score
from scoring.score_a import calculate_score_a, distance_score
from scoring.score_b import calculate_score_b
from scoring.score_c import calculate_score_c
from matching.hungarian import run_hungarian, build_cost_matrix
from models.candidate import Candidate, AcademicBackground, MilitaryRole
from models.school import School
from models.company import Company


# --- Fixtures ---

def make_candidate(**kwargs) -> Candidate:
    defaults = dict(
        id="C001",
        name="נועם",
        eli5_score=80.0,
        subject="סייבר",
        additional_subjects=["פייתון"],
        distance_km=10.0,
        family_status_score=80.0,
        commitment_score=90.0,
        career_switches=1,
        willing_periphery=False,
        tech_test_score=85.0,
        academic_background=AcademicBackground.TECH_UNIT,
        independent_courses=3,
        promotion_rate=80.0,
        military_role=MilitaryRole.TECH_LEAD,
        team_size=8,
        conflict_resolution_score=75.0,
        preferred_company_size="mid",
        work_style="agile",
        preferred_location="תל אביב",
        willing_relocate=False,
        tech_stack=["Python", "React"],
        years_experience=2.0,
    )
    defaults.update(kwargs)
    return Candidate(**defaults)


def make_school(**kwargs) -> School:
    defaults = dict(
        id="S001",
        name="בית ספר א'",
        location="תל אביב",
        lat=32.0,
        lng=34.8,
        required_subjects=["סייבר", "פייתון"],
        grade_levels=["ט", "י", "יא"],
        socioeconomic_rank=3,
        nurturing_index=4,
        months_without_teacher=6,
        budget_available=True,
    )
    defaults.update(kwargs)
    return School(**defaults)


def make_company(**kwargs) -> Company:
    defaults = dict(
        id="CO001",
        name="חברת הייטק",
        location="תל אביב",
        lat=32.0,
        lng=34.8,
        size="mid",
        work_style="agile",
        tech_stack=["Python", "React", "Node.js"],
        open_positions=2,
        urgency_score=70.0,
        willing_station_b=True,
        placement_fee_paid=False,
    )
    defaults.update(kwargs)
    return Company(**defaults)


# === VOLUME TESTS ===

def test_volume_perfect_scores():
    result = calculate_volume_score(95, 95, 95)
    assert result["passes_threshold"] is True
    assert result["volume_score"] > 80

def test_volume_one_below_threshold():
    result = calculate_volume_score(95, 95, 59)  # 59 < 60 = לא עובר
    assert result["passes_threshold"] is False
    assert result["final_score"] == 0.0

def test_volume_all_below_threshold():
    result = calculate_volume_score(59, 59, 59)
    assert result["passes_threshold"] is False

def test_volume_medium_scores():
    result = calculate_volume_score(75, 75, 75)
    assert result["passes_threshold"] is True
    assert 30 < result["volume_score"] < 60  # ∛(15³)/40×100 = 37.5

def test_volume_final_score_range():
    result = calculate_volume_score(80, 80, 80)
    assert 0 <= result["final_score"] <= 100


# === DISTANCE TESTS ===

def test_distance_under_10():
    assert distance_score(5, False) == 100.0

def test_distance_10_to_25():
    assert distance_score(15, False) == 80.0

def test_distance_25_to_40():
    assert distance_score(30, False) == 60.0

def test_distance_40_to_60():
    assert distance_score(50, False) == 35.0

def test_distance_over_60():
    assert distance_score(70, False) == 10.0

def test_distance_willing_periphery():
    assert distance_score(100, True) == 100.0


# === SCORE A TESTS ===

def test_score_a_range():
    c = make_candidate()
    s = make_school()
    score = calculate_score_a(c, s)
    assert 0 <= score <= 100

def test_score_a_subject_match():
    c = make_candidate(subject="סייבר")
    s = make_school(required_subjects=["סייבר"])
    score_match = calculate_score_a(c, s)

    c2 = make_candidate(subject="ביולוגיה")
    score_no_match = calculate_score_a(c2, s)

    assert score_match > score_no_match

def test_score_a_periphery_bonus():
    c = make_candidate(distance_km=80, willing_periphery=True)
    s = make_school()
    score = calculate_score_a(c, s)
    assert score > 0


# === SCORE B TESTS ===

def test_score_b_range():
    c = make_candidate()
    co = make_company()
    score = calculate_score_b(c, co)
    assert 0 <= score <= 100

def test_score_b_tech_match():
    c = make_candidate(tech_stack=["Python", "React"])
    co = make_company(tech_stack=["Python", "React"])
    score_match = calculate_score_b(c, co)

    c2 = make_candidate(tech_stack=["Java", "Kotlin"])
    score_no_match = calculate_score_b(c2, co)

    assert score_match > score_no_match

def test_score_b_leadership():
    c_commander = make_candidate(military_role=MilitaryRole.UNIT_COMMANDER)
    c_soldier = make_candidate(military_role=MilitaryRole.SOLDIER)
    co = make_company()

    score_commander = calculate_score_b(c_commander, co)
    score_soldier = calculate_score_b(c_soldier, co)

    assert score_commander > score_soldier


# === SCORE C TESTS ===

def test_score_c_range():
    c = make_candidate()
    s = make_school()
    co = make_company()
    score_c = calculate_score_c(75, 75, c, s, co)
    assert 0 <= score_c <= 100

def test_score_c_min_ab():
    c = make_candidate()
    s = make_school()
    co = make_company()
    c1 = calculate_score_c(90, 60, c, s, co)
    c2 = calculate_score_c(60, 90, c, s, co)
    assert abs(c1 - c2) < 5  # min(A,B) זהה


# === HUNGARIAN TESTS ===

def test_hungarian_basic():
    candidates = ["C1", "C2", "C3"]
    placements = ["P1", "P2", "P3"]
    scores = [
        [90, 50, 30],
        [40, 85, 20],
        [10, 30, 75],
    ]
    results = run_hungarian(candidates, placements, scores)
    assert len(results) == 3
    assigned_candidates = [r["candidate_id"] for r in results]
    assert "C1" in assigned_candidates

def test_hungarian_zero_scores_excluded():
    candidates = ["C1", "C2"]
    placements = ["P1", "P2"]
    scores = [
        [0, 80],
        [70, 0],
    ]
    results = run_hungarian(candidates, placements, scores)
    for r in results:
        assert r["final_score"] > 0

def test_hungarian_empty():
    results = run_hungarian([], [], [])
    assert results == []


# === INTEGRATION TEST ===

def test_full_pipeline():
    from main import run_full_matching
    from data.synthetic import generate_dataset

    candidates, schools, companies = generate_dataset(5, 3, 3)
    results = run_full_matching(candidates, schools, companies)

    assert "assignments" in results
    assert "total_value" in results
    assert results["total_value"] >= 0
    assert len(results["assignments"]) <= len(candidates)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
