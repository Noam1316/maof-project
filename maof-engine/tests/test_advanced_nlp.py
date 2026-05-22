"""
Tests — Advanced NLP Layer
מעוף Tech-Lead Israel

מכסה:
  - Semantic Match (subject + tech stack)
  - ELI5 Chatbot (adaptive session)
  - Code Test (adaptive technical questions)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from nlp.semantic_match import (
    semantic_similarity_simple,
    get_semantic_similarity,
    subject_semantic_score,
    tech_stack_semantic_score,
)
from nlp.eli5_chatbot import (
    run_adaptive_session,
    get_next_question,
    get_questions,
    LEVEL_SCORES,
)
from nlp.code_test import (
    run_code_test,
    get_first_question,
)


# ─── Semantic Match ───────────────────────────────────────────────

def test_semantic_exact_match():
    """מונחים זהים → similarity גבוהה"""
    score = semantic_similarity_simple(["Python"], ["Python"])
    assert score == 1.0

def test_semantic_synonym_hebrew_english():
    """עברית ↔ אנגלית → similarity גבוהה דרך נרדפות"""
    score = semantic_similarity_simple(["סייבר"], ["cyber"])
    assert score > 0.5

def test_semantic_synonym_paraphrase():
    """אבטחת מידע ↔ סייבר → נרדפות"""
    score = semantic_similarity_simple(["אבטחת מידע"], ["סייבר"])
    assert score > 0.3

def test_semantic_no_overlap():
    """Java ↔ Python — אין חפיפה"""
    score = semantic_similarity_simple(["Java", "Spring"], ["Python", "Django"])
    assert score == 0.0

def test_semantic_empty_lists():
    score = semantic_similarity_simple([], ["Python"])
    assert score == 0.0

def test_get_similarity_returns_keys():
    result = get_semantic_similarity(["Python", "AI"], ["Machine Learning", "Python"])
    assert "score" in result
    assert "method" in result
    assert "normalized" in result
    assert 0 <= result["normalized"] <= 100

def test_subject_semantic_score_exact():
    score = subject_semantic_score(["סייבר", "פייתון"], ["סייבר"])
    assert score >= 80.0

def test_subject_semantic_score_synonym():
    score = subject_semantic_score(["cyber"], ["סייבר"])
    assert score >= 60.0

def test_subject_semantic_score_no_match():
    score = subject_semantic_score(["מתמטיקה"], ["סייבר"])
    assert score < 50.0

def test_subject_semantic_empty_required():
    score = subject_semantic_score(["סייבר"], [])
    assert score == 80.0  # ברירת מחדל כשאין דרישות

def test_tech_stack_semantic_exact():
    score = tech_stack_semantic_score(["Python", "AI"], ["Python", "AI"])
    assert score >= 80.0

def test_tech_stack_semantic_synonyms():
    score = tech_stack_semantic_score(["פייתון", "נתונים"], ["Python", "Data Science"])
    assert score >= 40.0

def test_tech_stack_semantic_no_overlap():
    score = tech_stack_semantic_score(["Java"], ["Python"])
    assert score == 0.0

def test_tech_stack_empty_company():
    score = tech_stack_semantic_score(["Python"], [])
    assert score == 80.0

def test_tech_stack_empty_candidate():
    score = tech_stack_semantic_score([], ["Python"])
    assert score == 20.0


# ─── ELI5 Chatbot ────────────────────────────────────────────────

def test_chatbot_good_answers_pass():
    """תשובות טובות → עובר + רמה גבוהה"""
    answers = [
        "סייבר זה כמו מנעול על הדלת של המחשב שלך. דמיין שהמחשב הוא בית — אנשים רעים רוצים להיכנס. אנשי הסייבר הם השומרים שמוודאים שאף אחד לא יכנס.",
        "וירוס זה כמו מחלה — מתפשט לקבצים. כופרה שונה — כמו גנב שנועל את הבית ודורש כסף. שניהם זדוניים אבל בדרכים שונות.",
    ]
    result = run_adaptive_session("סייבר", answers)
    assert result["questions_asked"] == 2
    assert result["final_level"] >= 2
    assert result["adaptive_score"] > 40

def test_chatbot_weak_answer_stops():
    """תשובה חלשה → עוצר מיד"""
    answers = [
        "סייבר מתמודד עם אתגרי אבטחת מידע בסביבות ארגוניות.",
    ]
    result = run_adaptive_session("סייבר", answers)
    assert result["questions_asked"] == 1
    assert result["final_level"] == 1

def test_chatbot_no_answers():
    """אפס תשובות → לא קורס"""
    result = run_adaptive_session("סייבר", [])
    assert result["questions_asked"] == 0
    assert result["adaptive_score"] == 0.0
    assert result["passed"] is False

def test_chatbot_returns_required_keys():
    result = run_adaptive_session("פייתון", ["פייתון זה שפה שמדברים עם המחשב כמו מתכון."])
    required = ["topic", "questions_asked", "final_level", "adaptive_score", "passed", "results", "summary"]
    for key in required:
        assert key in result, f"Missing key: {key}"

def test_chatbot_score_range():
    answers = ["פייתון זה כמו מתכון שהמחשב מבין. דמיין שאתה מכין עוגה — כל שורה היא הוראה."]
    result = run_adaptive_session("פייתון", answers)
    assert 0 <= result["adaptive_score"] <= 100

def test_chatbot_topic_fallback():
    """נושא לא מוכר → default questions"""
    result = run_adaptive_session("בלוקצ'יין", ["הסברתי את הנושא בצורה ברורה עם דוגמאות מחיי יום-יום."])
    assert result["questions_asked"] >= 1

def test_chatbot_max_level_is_5():
    questions = get_questions("סייבר")
    assert len(questions) == 5

def test_chatbot_get_next_question():
    q = get_next_question("פייתון", 0)
    assert q is not None
    assert "question" in q
    assert "level" in q

def test_chatbot_level_scores_ordered():
    levels = sorted(LEVEL_SCORES.keys())
    scores = [LEVEL_SCORES[l] for l in levels]
    assert scores == sorted(scores)  # ציונים עולים עם הרמה


# ─── Code Test ───────────────────────────────────────────────────

def test_code_test_good_answers():
    """תשובות טובות → עובר"""
    answers = [
        "ההבדל: list ניתן לשינוי (mutable), tuple לא. כשנתונים קבועים — tuple מהיר יותר. דוגמה: קואורדינטות = tuple, רשימת משתמשים = list.",
        "decorator זה עטיפה סביב פונקציה. כמו @login_required שבודק שהמשתמש מחובר לפני כל קריאה. הוא מוסיף פונקציונליות בלי לשנות את הקוד.",
    ]
    result = run_code_test(answers, ["Python"])
    assert result["questions_asked"] == 2
    assert result["final_level"] >= 2

def test_code_test_weak_answer():
    """תשובה חלשה → עוצר"""
    result = run_code_test(["list ו-tuple הם שניהם אוספים."], ["Python"])
    assert result["questions_asked"] == 1
    assert result["passed"] is False

def test_code_test_no_answers():
    result = run_code_test([], ["Python"])
    assert result["adaptive_score"] == 0.0
    assert result["passed"] is False

def test_code_test_domain_detection_python():
    result = run_code_test(["תשובה כלשהי על list ו-tuple ופייתון."], ["Python", "Django"])
    assert result["domain"] == "python"

def test_code_test_domain_detection_cyber():
    result = run_code_test(["authentication זה אימות זהות, authorization זה הרשאות."], ["Cyber", "Security"])
    assert result["domain"] == "cyber"

def test_code_test_domain_detection_data():
    result = run_code_test(["mean זה ממוצע, median זה חציון — חציון עמיד יותר לערכים קיצוניים."], ["Data Science", "ML"])
    assert result["domain"] == "data"

def test_code_test_domain_default():
    result = run_code_test(["תשובה כלשהי."], [])
    assert result["domain"] == "default"

def test_code_test_returns_required_keys():
    result = run_code_test(["תשובה."], ["Python"])
    required = ["domain", "questions_asked", "final_level", "adaptive_score", "passed", "results", "summary"]
    for key in required:
        assert key in result, f"Missing key: {key}"

def test_code_test_score_range():
    result = run_code_test(["ההבדל בין list לבין tuple הוא שlist ניתן לשינוי."], ["Python"])
    assert 0 <= result["adaptive_score"] <= 100

def test_code_test_first_question():
    q = get_first_question(["Python"])
    assert "question" in q
    assert "domain" in q
    assert q["domain"] == "python"

def test_code_test_first_question_no_stack():
    q = get_first_question([])
    assert "question" in q
    assert q["domain"] == "default"

def test_code_test_next_question_provided():
    """אם עובר → next_question מסופק"""
    good_answer = "ההבדל המרכזי: list ניתן לשינוי (mutable) ו-tuple לא. כשנתונים קבועים — tuple מהיר יותר ומוגן. דוגמה: קואורדינטות GPS = tuple כי לא משתנות. רשימת משתמשים = list כי משתנה."
    result = run_code_test([good_answer], ["Python"])
    if result["results"][0]["passes"]:
        assert result["next_question"] is not None
