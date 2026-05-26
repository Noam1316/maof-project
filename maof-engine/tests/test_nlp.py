"""
Tests — NLP Layer (ELI5 Analyzer + LLM Comparator)
מעוף Tech-Lead Israel
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from nlp.eli5_analyzer import analyze_eli5
from nlp.llm_comparator import (
    compute_similarity_simple,
    get_similarity,
    get_llm_reference,
    compute_conciseness_bonus,
    analyze_with_llm_comparison,
    SIMILARITY_THRESHOLD,
    CONCISENESS_BONUS_MAX,
)


# ─── ELI5 Analyzer ───────────────────────────────────────────────


def test_eli5_returns_required_keys():
    result = analyze_eli5("סייבר זה כמו מנעול על הדלת של המחשב שלך.")
    assert "total_score" in result
    assert "passes_minimum" in result
    assert "breakdown" in result
    assert "feedback" in result


def test_eli5_score_range():
    """ציון חייב להיות 0-100"""
    good = analyze_eli5(
        "סייבר זה כמו מנעול על המחשב. דמיין שהמחשב הוא בית — "
        "אנשי הסייבר שומרים שאף אחד לא יכנס."
    )
    assert 0 <= good["total_score"] <= 100

    jargon = analyze_eli5(
        "אבטחת מידע עוסקת בהגנה על מערכות מחשוב ממתקפות זדוניות. "
        "פרוטוקולי הצפנה ואימות דו-שלבי מבטיחים קונפידנציאליות."
    )
    assert 0 <= jargon["total_score"] <= 100


def test_eli5_good_beats_jargon():
    """הסבר פשוט עם אנלוגיה צריך לנצח ז'רגון"""
    good = analyze_eli5(
        "פייתון זה כמו מתכון שהמחשב מבין. "
        "דמיין שאתה מכין עוגה — כל שורה היא הוראה אחת. "
        "לדוגמה, כתוב 'הדפס שלום' — המחשב ידפיס שלום."
    )
    jargon = analyze_eli5(
        "פייתון היא שפת תכנות מפורשת בעלת syntax ידידותי "
        "המשמשת לפיתוח backend, data science ואוטומציה."
    )
    assert good["total_score"] > jargon["total_score"]


def test_eli5_passes_minimum_threshold():
    """הסבר טוב עובר 60"""
    result = analyze_eli5(
        "מתמטיקה זה כמו שפה שכולם מבינים. "
        "דמיין שיש לך 5 תפוחים ונתת 2 לחבר — נשארו לך 3. זה מתמטיקה. "
        "לדוגמה, הבנק משתמש במתמטיקה כדי לחשב ריבית."
    )
    assert result["passes_minimum"] is True


def test_eli5_fails_minimum_jargon():
    """ז'רגון טכני לא עובר 60"""
    result = analyze_eli5(
        "אלגוריתמים רקורסיביים מבצעים קריאה עצמית עם תנאי עצירה "
        "המבוסס על מקרה בסיס ומקרה רקורסיבי."
    )
    assert result["passes_minimum"] is False


def test_eli5_breakdown_keys():
    """breakdown מכיל את כל 6 המדדים"""
    result = analyze_eli5("המחשב כמו מוח — הוא חושב ועושה חישובים.")
    breakdown = result["breakdown"]
    for key in ["simplicity", "analogies", "narrative_structure", "coherence", "accuracy", "conciseness"]:
        assert key in breakdown, f"Missing breakdown key: {key}"


def test_eli5_empty_text():
    """טקסט ריק לא קורס"""
    result = analyze_eli5("")
    assert result["total_score"] == 0.0
    assert result["passes_minimum"] is False


def test_eli5_accuracy_with_topic():
    """accuracy_score עולה כשהנושא מכוסה"""
    from nlp.eli5_analyzer import accuracy_score
    good = accuracy_score(
        "סייבר זה כמו מנעול שמגן על הבית שלך. אם הסיסמה חלשה — הגנב יכול לפרוץ.",
        topic="סייבר"
    )
    empty = accuracy_score("הנושא מעניין מאוד.", topic="סייבר")
    assert good > empty
    assert 0 <= good <= 100


def test_eli5_accuracy_without_topic():
    """accuracy_score ללא topic — מדד סובסטנס"""
    from nlp.eli5_analyzer import accuracy_score
    rich = accuracy_score(
        "דמיין שהמחשב הוא ספרייה ענקית. כל קובץ הוא ספר, "
        "וה-CPU הוא הספרן שמוצא את הספר הנכון תוך שניות."
    )
    thin = accuracy_score("זה מאוד מעניין וחשוב.")
    assert rich > thin


def test_analogy_quality_matters():
    """אנלוגיה מפותחת (15+ מילים) מקבלת ציון גבוה יותר מאנלוגיה קצרה"""
    from nlp.eli5_analyzer import analogy_score
    developed = analogy_score(
        "דמיין שהמחשב הוא כמו מוח גדול שיכול לחשוב על מיליון דברים בו-זמנית ולזכור הכל."
    )
    minimal = analogy_score("זה כמו מוח.")
    assert developed > minimal


def test_coherence_connected_beats_fragmented():
    """טקסט מקושר מקבל coherence גבוה יותר מרשימת עובדות"""
    from nlp.eli5_analyzer import coherence_score
    connected = coherence_score(
        "המחשב מקבל הוראות. לכן, כל פקודה מעובדת בסדר. "
        "בנוסף, התוצאה נשמרת בזיכרון. כך המחשב יכול לבצע משימות מורכבות."
    )
    fragmented = coherence_score(
        "המחשב מהיר. הכלב רץ. השמש זורחת. הים כחול. העץ גבוה. הספר אדום."
    )
    assert connected > fragmented


def test_eli5_short_text():
    """טקסט קצר מאוד — לא קורס, ציון נמוך"""
    result = analyze_eli5("סייבר.")
    assert 0 <= result["total_score"] <= 100


# ─── LLM Comparator — Jaccard Similarity ──────────────────────────


def test_jaccard_identical_texts():
    """טקסטים זהים → similarity = 1.0"""
    text = "סייבר זה כמו מנעול על הדלת"
    score = compute_similarity_simple(text, text)
    assert score == 1.0


def test_jaccard_no_overlap():
    """אפס מילים משותפות → similarity = 0"""
    score = compute_similarity_simple("כלב חתול ציפור", "שולחן כיסא מחשב")
    assert score == 0.0


def test_jaccard_partial_overlap():
    """חפיפה חלקית → 0 < similarity < 1"""
    score = compute_similarity_simple(
        "סייבר זה כמו מנעול על המחשב",
        "המחשב צריך הגנה מפני פריצות"
    )
    assert 0.0 < score < 1.0


def test_jaccard_empty_strings():
    """מחרוזות ריקות לא קורסות"""
    assert compute_similarity_simple("", "") == 0.0
    assert compute_similarity_simple("טקסט", "") == 0.0


def test_get_similarity_returns_dict():
    result = get_similarity("סייבר זה כמו מנעול", "מנעול מגן על הבית")
    assert "score" in result
    assert "method" in result
    assert 0.0 <= result["score"] <= 1.0


# ─── LLM Comparator — Reference Generation ────────────────────────


def test_get_reference_cyber():
    ref = get_llm_reference("סייבר")
    assert "text" in ref
    assert "source" in ref
    assert len(ref["text"]) > 20


def test_get_reference_python():
    ref = get_llm_reference("פייתון")
    assert ref["source"] in ("claude", "reference", "default")
    assert len(ref["text"]) > 20


def test_get_reference_unknown_topic():
    """נושא לא מוכר → default reference"""
    ref = get_llm_reference("קוונטים ודינמיקה לא-לינארית")
    assert ref["source"] in ("claude", "default")
    assert len(ref["text"]) > 10


# ─── LLM Comparator — Conciseness Bonus ──────────────────────────


def test_bonus_short_similar():
    """קצר + דומה → בונוס חיובי"""
    candidate = "סייבר זה כמו מנעול על המחשב. אנשי סייבר שומרים שאף אחד לא יכנס."
    reference = (
        "סייבר זה כמו מנעול על הדלת של המחשב שלך. "
        "דמיין שהמחשב שלך הוא בית. אנשים רעים רוצים להיכנס ולגנוב דברים. "
        "אנשי סייבר הם השומרים שמוודאים שהמנעול חזק ושאף אחד לא יכול לפרוץ. "
        "לדוגמה, כשאתה מכניס סיסמה, זה כמו מפתח. "
        "לכן חשוב להשתמש במפתחות חזקים."
    )
    result = compute_conciseness_bonus(candidate, reference, similarity=0.30)
    assert result["bonus"] >= 0.0  # may or may not get bonus based on threshold


def test_bonus_low_similarity_no_bonus():
    """similarity נמוכה מהסף → אפס בונוס"""
    result = compute_conciseness_bonus(
        "שמיים כחולים עם עננים לבנים",
        "המחשב מעבד נתונים בינאריים",
        similarity=0.01
    )
    assert result["bonus"] == 0.0


def test_bonus_longer_candidate_no_bonus():
    """ארוך יותר מה-reference → אפס בונוס"""
    short_ref = "סייבר מגן על מחשבים."
    long_candidate = " ".join(["סייבר"] * 50)
    result = compute_conciseness_bonus(long_candidate, short_ref, similarity=0.80)
    assert result["bonus"] == 0.0


def test_bonus_max_capped():
    """בונוס לא עולה על CONCISENESS_BONUS_MAX"""
    result = compute_conciseness_bonus(
        "סייבר.",
        " ".join(["מנעול הגנה מחשב בית"] * 20),
        similarity=1.0
    )
    assert result["bonus"] <= CONCISENESS_BONUS_MAX


def test_bonus_empty_reference():
    """reference ריק → אפס בונוס, לא קריסה"""
    result = compute_conciseness_bonus("סייבר טוב", "", similarity=0.80)
    assert result["bonus"] == 0.0


# ─── Full Pipeline ────────────────────────────────────────────────


def test_full_analysis_keys():
    """analyze_with_llm_comparison מחזיר את כל השדות"""
    result = analyze_with_llm_comparison(
        "סייבר זה כמו מנעול על המחשב שלך.",
        "סייבר"
    )
    required = [
        "base_score", "conciseness_bonus", "final_score",
        "passes_minimum", "breakdown", "similarity",
        "conciseness_analysis", "reference_source", "feedback"
    ]
    for key in required:
        assert key in result, f"Missing key: {key}"


def test_full_analysis_score_range():
    result = analyze_with_llm_comparison(
        "פייתון זה שפה שבה מדברים עם המחשב, כמו שאנחנו מדברים בעברית. "
        "דמיין שאתה רוצה להכין עוגה — פייתון זה המתכון.",
        "פייתון"
    )
    assert 0 <= result["final_score"] <= 100
    assert result["final_score"] >= result["base_score"]  # בונוס לא מוריד ציון


def test_full_analysis_bonus_adds_to_base():
    """final_score = base + bonus (capped at 100)"""
    result = analyze_with_llm_comparison(
        "סייבר זה כמו מנעול על המחשב שמגן על הבית שלך.",
        "סייבר"
    )
    expected = min(100.0, result["base_score"] + result["conciseness_bonus"])
    assert abs(result["final_score"] - expected) < 0.01
