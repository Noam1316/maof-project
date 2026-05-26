"""
Tests — Assessment Pipeline (complete-assessment endpoint)
מעוף Tech-Lead Israel
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app import app
from database import repository as db

client = TestClient(app)

CANDIDATE_BASE = {
    "id": "test-pipeline-001",
    "name": "יוסי כהן",
    "eli5_score": 0.0,
    "subject": "סייבר",
    "additional_subjects": [],
    "distance_km": 10,
    "family_status_score": 70,
    "commitment_score": 80,
    "career_switches": 1,
    "willing_periphery": False,
    "tech_test_score": 0.0,
    "academic_background": "warriors_tech",
    "independent_courses": 2,
    "promotion_rate": 70,
    "military_role": "tech_lead",
    "team_size": 5,
    "conflict_resolution_score": 75,
    "preferred_company_size": "mid",
    "work_style": "hybrid",
    "preferred_location": "tel_aviv",
    "willing_relocate": False,
    "tech_stack": ["python", "cyber"],
    "years_experience": 3,
    "systemic_score": 0.0,
    "code_score": 0.0,
}


def _create():
    db.upsert_candidate(CANDIDATE_BASE.copy())


def test_complete_assessment_full():
    """פייפליין מלא — כל שלושת הציונים"""
    _create()
    r = client.post("/api/v1/candidates/test-pipeline-001/complete-assessment", json={
        "eli5_score": 78,
        "code_score": 65,
        "systemic_score": 82,
        "topic": "סייבר",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["eli5_score"] == 78.0
    assert data["code_score"] == 65.0
    assert data["systemic_score"] == 82.0
    # tech_test = 82*0.55 + 65*0.45 = 45.1 + 29.25 = 74.35
    assert abs(data["tech_test_score"] - 74.35) < 0.1
    assert data["pipeline_complete"] is True


def test_complete_assessment_eli5_only():
    """רק ELI5 — tech_test_score לא משתנה"""
    _create()
    r = client.post("/api/v1/candidates/test-pipeline-001/complete-assessment", json={
        "eli5_score": 85,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["eli5_score"] == 85.0
    assert data["pipeline_complete"] is False  # tech_test עדיין 0


def test_complete_assessment_systemic_only():
    """רק systemic — tech_test = systemic"""
    _create()
    r = client.post("/api/v1/candidates/test-pipeline-001/complete-assessment", json={
        "systemic_score": 70,
    })
    assert r.status_code == 200
    assert r.json()["tech_test_score"] == 70.0


def test_complete_assessment_not_found():
    """מועמד לא קיים → 404"""
    r = client.post("/api/v1/candidates/nonexistent-999/complete-assessment", json={
        "eli5_score": 80,
    })
    assert r.status_code == 404


def test_complete_assessment_invalid_score():
    """ציון מחוץ לטווח → 400"""
    _create()
    r = client.post("/api/v1/candidates/test-pipeline-001/complete-assessment", json={
        "eli5_score": 150,
    })
    assert r.status_code == 400


def test_complete_assessment_persists():
    """הציון נשמר ב-DB ואפשר לקרוא אחרי"""
    _create()
    client.post("/api/v1/candidates/test-pipeline-001/complete-assessment", json={
        "eli5_score": 91,
        "systemic_score": 88,
        "code_score": 72,
    })
    saved = db.get_candidate("test-pipeline-001")
    assert saved["eli5_score"] == 91.0
    assert saved["systemic_score"] == 88.0
    assert saved["code_score"] == 72.0


def test_candidate_model_has_new_fields():
    """Candidate model מכיל את השדות החדשים"""
    from models.candidate import Candidate
    fields = Candidate.model_fields
    assert "systemic_score" in fields
    assert "code_score" in fields


def test_blend_weights():
    """כשיש שני מבחנים — blend 55/45. כשיש אחד — מלא ללא עונש."""
    _create()
    # שני מבחנים — blend
    r = client.post("/api/v1/candidates/test-pipeline-001/complete-assessment", json={
        "systemic_score": 100,
        "code_score": 100,
    })
    assert r.json()["tech_test_score"] == 100.0

    r = client.post("/api/v1/candidates/test-pipeline-001/complete-assessment", json={
        "systemic_score": 80,
        "code_score": 60,
    })
    # 80*0.55 + 60*0.45 = 44 + 27 = 71
    assert abs(r.json()["tech_test_score"] - 71.0) < 0.1

    # מבחן יחיד — לא מעניש (מאפס ידנית לפני)
    _create()
    r = client.post("/api/v1/candidates/test-pipeline-001/complete-assessment", json={
        "systemic_score": 90,
    })
    assert r.json()["tech_test_score"] == 90.0
