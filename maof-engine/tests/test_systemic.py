"""
Tests — Systemic Thinking Test
מעוף Tech-Lead Israel
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from nlp.systemic_test import (
    get_opening_question,
    get_next_question,
    score_chain,
    MAX_QUESTIONS,
)

GOOD_ANSWER = (
    "Authentication זה תהליך שבו מערכת מוודאת שאתה מי שאתה אומר שאתה. "
    "כמו מנעול על הדלת — אתה צריך מפתח. הסיסמה היא המפתח, "
    "והשרת בודק שהמפתח תואם לרשומה שיש לו."
)

THIN_ANSWER = "זה מאוד מעניין ומורכב."


# ── Opening question ──────────────────────────────────────────────

def test_opening_returns_question():
    q = get_opening_question("סייבר")
    assert "question" in q
    assert len(q["question"]) > 10
    assert q["question_index"] == 1


def test_opening_unknown_topic():
    q = get_opening_question("קוואנטים")
    assert "question" in q
    assert q["question_index"] == 1


def test_opening_partial_match():
    q = get_opening_question("פייתון ולמידת מכונה")
    assert "question" in q


# ── Next question ─────────────────────────────────────────────────

def test_next_question_fallback():
    """בלי Groq — מחזיר fallback"""
    qa = [{"question": "מה זה auth?", "answer": GOOD_ANSWER}]
    result = get_next_question("סייבר", qa)
    assert "question" in result
    assert result["question_index"] == 2


def test_next_question_increments_index():
    qa = [
        {"question": "Q1", "answer": GOOD_ANSWER},
        {"question": "Q2", "answer": GOOD_ANSWER},
    ]
    result = get_next_question("סייבר", qa)
    assert result["question_index"] == 3


def test_next_question_done_after_max():
    qa = [{"question": f"Q{i}", "answer": GOOD_ANSWER} for i in range(MAX_QUESTIONS)]
    result = get_next_question("סייבר", qa)
    assert result.get("done") is True


def test_next_question_empty_qa():
    """רשימה ריקה → fallback שאלה ראשונה"""
    result = get_next_question("פייתון", [])
    assert "question" in result
    assert result["question_index"] == 1


# ── Score chain ───────────────────────────────────────────────────

def test_score_returns_required_keys():
    qa = [{"question": "מה זה auth?", "answer": GOOD_ANSWER}]
    result = score_chain("סייבר", qa)
    for key in ["total_score", "passes_minimum", "depth_score",
                "coverage_score", "consistency", "per_answer"]:
        assert key in result, f"Missing key: {key}"


def test_score_range():
    qa = [{"question": "Q", "answer": GOOD_ANSWER}]
    result = score_chain("סייבר", qa)
    assert 0 <= result["total_score"] <= 100


def test_score_empty():
    result = score_chain("סייבר", [])
    assert result["total_score"] == 0.0


def test_good_answers_beat_thin():
    good_qa = [{"question": "Q", "answer": GOOD_ANSWER}] * 3
    thin_qa = [{"question": "Q", "answer": THIN_ANSWER}]  * 3
    assert score_chain("סייבר", good_qa)["total_score"] > \
           score_chain("סייבר", thin_qa)["total_score"]


def test_more_answers_tracked():
    qa = [{"question": f"Q{i}", "answer": GOOD_ANSWER} for i in range(4)]
    result = score_chain("סייבר", qa)
    assert result["questions_answered"] == 4


def test_per_answer_length():
    qa = [{"question": f"Q{i}", "answer": GOOD_ANSWER} for i in range(3)]
    result = score_chain("פייתון", qa)
    assert len(result["per_answer"]) == 3
    for item in result["per_answer"]:
        assert "score" in item
        assert "index" in item
