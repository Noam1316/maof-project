"""
ELI5 Analyzer — NLP לניתוח יכולת הסבר
מעוף Tech-Lead Israel

מנתח טקסט לפי 5 מדדים:
  1. פשטות      — Flesch-like + אורך מילים ומשפטים
  2. אנלוגיות   — זיהוי "כמו", "דמיין", "זה דומה ל"
                 שדרוג: מילה סופרת רק אם משמשת בהקשר אמיתי (≥6 מילים במשפט)
  3. נרטיב      — Hook בפתיחה + מסקנה בסיום (מבנה, לא רשימת מילים)
  4. קוהרנטיות  — קשר בין משפטים
  5. תמציתיות   — פחות מילים לאותו רעיון + TTR + filler detection

ללא API Key — keyword-based analysis בלבד.
"""

import re
import math
from typing import Dict, List


# --- מילות אנלוגיה ---
ANALOGY_KEYWORDS_HE = [
    "כמו", "דמיין", "דמיינו", "זה דומה ל", "בדיוק כמו",
    "תחשוב על", "תחשבו על", "לדוגמה", "למשל", "נגיד",
    "נניח", "נדמה", "משל", "דומה ל", "בדומה ל",
    "זה כאילו", "כאילו", "כאלו", "ממש כמו",
]

ANALOGY_KEYWORDS_EN = [
    "like", "imagine", "just like", "similar to", "think of",
    "for example", "for instance", "such as", "as if",
    "picture", "consider", "suppose", "say you", "pretend",
]

# --- מילות חיבור (קוהרנטיות) ---
COHERENCE_KEYWORDS_HE = [
    "לכן", "כי", "בגלל", "אז", "לפיכך", "כתוצאה",
    "ראשית", "שנית", "לסיום", "בנוסף", "יתרה מזאת",
    "לעומת זאת", "אם כן", "מכאן ש",
]

COHERENCE_KEYWORDS_EN = [
    "therefore", "because", "so", "thus", "hence", "first",
    "second", "finally", "additionally", "moreover", "however",
    "in conclusion", "as a result", "for this reason",
]


# --- Hook keywords (opening invitation) ---
HOOK_KEYWORDS_HE = [
    "דמיין", "דמיינו", "תחשוב", "תחשבו", "נניח", "נגיד",
    "שאלה", "למה", "איך", "האם ידעת",
    "בוא נגיד", "בואו נגיד", "חשבת פעם",
]
HOOK_KEYWORDS_EN = [
    "imagine", "suppose", "picture", "have you ever", "why does",
    "what if", "let's say", "did you know", "ever wonder", "think about",
]

# --- Conclusion keywords (closing takeaway) ---
CONCLUSION_KEYWORDS_HE = [
    "לכן", "לסיכום", "לסיום", "מכאן ש",
    "לפיכך", "ולכן", "כלומר", "בקצרה", "בגדול",
    "אז בעצם", "זאת אומרת",
]
CONCLUSION_KEYWORDS_EN = [
    "therefore", "in conclusion", "so basically", "in short",
    "the bottom line", "to summarize", "in other words",
    "ultimately", "that's why", "which means",
]

# --- מילות מילוי (filler) — מנפחות בלי להוסיף תוכן ---
FILLER_PHRASES_HE = [
    "כמובן", "בגדול", "למעשה", "כאמור", "כידוע", "בין היתר",
    "מן הסתם", "אחרי הכל", "בסופו של דבר", "חשוב לציין",
    "כדאי לציין", "ראוי לציין", "מעניין לציין",
]

FILLER_PHRASES_EN = [
    "basically", "obviously", "needless to say", "as mentioned",
    "it is worth noting", "it goes without saying", "first and foremost",
    "last but not least", "at the end of the day",
]

# --- מילים ז'רגוניסטיות (מורידות ציון) ---
JARGON_HE = [
    "אלגוריתם", "פרמטר", "מטריקס", "פרוטוקול", "ממשק",
    "אינטגרציה", "מודול", "דאטה", "ביג דאטה", "מל",
]

JARGON_EN = [
    "algorithm", "parameter", "matrix", "protocol", "interface",
    "integration", "module", "dataset", "machine learning",
    "neural network", "gradient", "epoch", "tensor",
]


def tokenize(text: str) -> List[str]:
    """פיצול לטוקנים בסיסי"""
    words = re.findall(r'\b[\w֐-׿]+\b', text)
    return [w for w in words if len(w) > 1]


def split_sentences(text: str) -> List[str]:
    """פיצול למשפטים"""
    sentences = re.split(r'[.!?。]\s*', text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]


# --- מדד 1: פשטות ---
def simplicity_score(text: str) -> float:
    """
    מבוסס על:
    - ממוצע אורך מילים (קצר = פשוט)
    - ממוצע אורך משפטים (קצר = פשוט)
    - מספר מילות ז'רגון
    """
    words = tokenize(text)
    sentences = split_sentences(text)

    if not words or not sentences:
        return 50.0

    avg_word_len = sum(len(w) for w in words) / len(words)
    avg_sentence_len = len(words) / len(sentences)

    # ציון אורך מילים (2-5 אותיות = אידיאלי)
    word_score = max(0, 100 - (avg_word_len - 4) * 15)

    # ציון אורך משפטים (8-15 מילים = אידיאלי)
    sentence_score = max(0, 100 - abs(avg_sentence_len - 12) * 5)

    # עונש ז'רגון
    all_jargon = JARGON_HE + JARGON_EN
    text_lower = text.lower()
    jargon_count = sum(1 for j in all_jargon if j.lower() in text_lower)
    jargon_penalty = min(40, jargon_count * 10)

    score = (word_score * 0.4 + sentence_score * 0.6) - jargon_penalty
    return round(max(0, min(100, score)), 2)


# --- עזר: בדיקת שימוש בהקשר אמיתי ---
def _keyword_in_real_context(keyword: str, sentences: List[str], min_words: int = 6) -> bool:
    """
    מחזיר True רק אם מילת המפתח מופיעה במשפט עם ≥min_words מילים.
    מונע keyword stuffing: "לדוגמה." לבד לא סופר.
    """
    kw_lower = keyword.lower()
    for sentence in sentences:
        if kw_lower in sentence.lower() and len(sentence.split()) >= min_words:
            return True
    return False


# --- מדד 2: אנלוגיות ---
def analogy_score(text: str) -> float:
    """
    מזהה שימוש במילות אנלוגיה ודוגמאות.
    שדרוג: מילה סופרת רק אם מופיעה בהקשר אמיתי (משפט עם ≥6 מילים).
    "לדוגמה." בודד — לא סופר. "לדוגמה, כשאתה לוחץ..." — כן סופר.
    """
    sentences = split_sentences(text)
    all_keywords = ANALOGY_KEYWORDS_HE + ANALOGY_KEYWORDS_EN

    # סינון: רק מילות אנלוגיה שמשמשות בהקשר משפטי אמיתי
    qualified = {
        kw for kw in all_keywords
        if _keyword_in_real_context(kw, sentences, min_words=6)
    }
    unique_found = len(qualified)

    # ציון: 0 = 20, 1 = 60, 2 = 80, 3+ = 100
    if unique_found == 0:
        return 20.0
    elif unique_found == 1:
        return 60.0
    elif unique_found == 2:
        return 80.0
    else:
        return min(100.0, 80 + unique_found * 5)


# --- מדד 3: מבנה נרטיבי (Hook + Conclusion) ---
def creativity_score(text: str) -> float:
    """Hook בפתיחה + מסקנה בסיום.
    עמיד בפני keyword-stuffing: מודד מבנה, לא רשימת מילים.

    hook בלבד          -> 70
    מסקנה בלבד         -> 50
    שניהם (מבנה שלם)   -> 100
    אף אחד             -> 20
    """
    words = text.split()
    if not words:
        return 20.0
    first = " ".join(words[:30]).lower()
    last  = " ".join(words[-40:]).lower()
    has_hook       = any(k.lower() in first for k in HOOK_KEYWORDS_HE + HOOK_KEYWORDS_EN)
    has_conclusion = any(k.lower() in last  for k in CONCLUSION_KEYWORDS_HE + CONCLUSION_KEYWORDS_EN)
    if has_hook and has_conclusion:
        return 100.0
    if has_hook:
        return 70.0
    if has_conclusion:
        return 50.0
    return 20.0


# --- מדד 4: קוהרנטיות ---
def coherence_score(text: str) -> float:
    """
    מזהה מילות חיבור ומבנה לוגי
    """
    text_lower = text.lower()
    sentences = split_sentences(text)

    if len(sentences) < 2:
        return 40.0

    all_coherence = COHERENCE_KEYWORDS_HE + COHERENCE_KEYWORDS_EN
    found = sum(1 for kw in all_coherence if kw.lower() in text_lower)

    # ציון בסיס לפי מספר משפטים
    structure_score = min(80, len(sentences) * 15)

    # בונוס מילות חיבור
    coherence_bonus = min(20, found * 8)

    return round(min(100, structure_score + coherence_bonus), 2)


# --- מדד 5: תמציתיות ---
def conciseness_score(text: str) -> float:
    """
    פחות מילים לאותו רעיון = ציון גבוה.
    מדדים:
      - חזרות מילים (חזרה >2 פעמים = עונש)
      - אורך כולל (קצר/ארוך מדי = עונש)
      - TTR (Type-Token Ratio) — ייחודיות: < 0.35 = טקסט חזרתי מדי
      - Filler phrases — מילים שמנפחות בלי תוכן
    """
    from collections import Counter
    words = tokenize(text)

    if not words:
        return 50.0

    # --- חזרות ---
    word_counts = Counter(w.lower() for w in words if len(w) > 3)
    repetitions = sum(1 for count in word_counts.values() if count > 2)
    repetition_penalty = min(30, repetitions * 10)

    # --- אורך כולל ---
    length_penalty = 0
    if len(words) < 20:
        length_penalty = 20   # קצר מדי
    elif len(words) > 150:
        length_penalty = 15   # ארוך מדי

    # --- TTR: Type-Token Ratio (ייחודיות מילים) ---
    # ערך תקין: 0.45-0.70. מתחת ל-0.35 → טקסט חזרתי/ממולא
    ttr_penalty = 0
    if len(words) > 15:
        ttr = len(set(w.lower() for w in words)) / len(words)
        if ttr < 0.35:
            ttr_penalty = int((0.35 - ttr) * 80)   # עד ~28 נקודות
            ttr_penalty = min(ttr_penalty, 25)

    # --- Filler phrases ---
    text_lower = text.lower()
    all_fillers = FILLER_PHRASES_HE + FILLER_PHRASES_EN
    filler_count = sum(1 for f in all_fillers if f.lower() in text_lower)
    filler_penalty = min(15, filler_count * 5)

    score = 100 - length_penalty - repetition_penalty - ttr_penalty - filler_penalty
    return round(max(0, min(100, score)), 2)


# --- ציון ELI5 מלא ---
def analyze_eli5(text: str) -> Dict:
    """
    מנתח טקסט ומחזיר ציון ELI5 מלא.

    Returns:
        dict עם ציון כולל + פירוט לפי מדד
    """
    if not text or len(text.strip()) < 10:
        return {
            "total_score": 0.0,
            "passes_minimum": False,
            "breakdown": {},
            "feedback": ["הטקסט קצר מדי לניתוח"]
        }

    simplicity = simplicity_score(text)
    analogies = analogy_score(text)
    creativity = creativity_score(text)
    coherence = coherence_score(text)
    conciseness = conciseness_score(text)

    # ציון משוקלל
    total = (
        simplicity * 0.30 +
        analogies * 0.30 +
        creativity * 0.15 +
        coherence * 0.15 +
        conciseness * 0.10
    )
    total = round(total, 2)

    # משוב אוטומטי
    feedback = []
    if simplicity < 60:
        feedback.append("השתמש במילים פשוטות יותר, הימנע מז'רגון")
    if analogies < 60:
        feedback.append("הוסף אנלוגיות — 'זה כמו...', 'דמיין ש...'")
    if creativity < 60:
        feedback.append("פתח עם שאלה/הזמנה ('דמיין ש...') וסיים עם מסקנה ('לכן', 'כלומר')")
    if coherence < 60:
        feedback.append("הוסף מילות חיבור — 'לכן', 'כי', 'בנוסף'")
    if conciseness < 60:
        feedback.append("נסה לקצר — פחות מילים לאותו רעיון")

    return {
        "total_score": total,
        "passes_minimum": total >= 60,
        "breakdown": {
            "simplicity": simplicity,
            "analogies": analogies,
            "narrative_structure": creativity,
            "coherence": coherence,
            "conciseness": conciseness,
        },
        "feedback": feedback if feedback else ["הסבר טוב! המשך כך"]
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    examples = [
        {
            "label": "הסבר טוב — עם אנלוגיות",
            "text": """
            מחשב זה בדיוק כמו מוח של אדם, אבל עשוי ממתכת ופלסטיק.
            דמיין שיש לך ספר רשימות ענק. בכל פעם שאתה רוצה משהו,
            המחשב מחפש בספר ומוצא את התשובה. לדוגמה, כשאתה לוחץ
            על כפתור, המחשב רואה זאת ומבין מה לעשות.
            לכן, ככל שהספר מאורגן יותר, המחשב מהיר יותר.
            """
        },
        {
            "label": "הסבר רע — ז'רגון ומורכבות",
            "text": """
            המחשב מבצע אופרציות בינאריות על ידי טרנזיסטורים
            המורכבים למעגלים אינטגרליים. הפרוצסור מבצע
            אינסטרוקציות מהמחסנית על ידי שימוש ב-ALU
            וב-control unit. הדאטה עובר דרך הבאס.
            """
        },
    ]

    for ex in examples:
        print(f"\n{'='*50}")
        print(f"דוגמה: {ex['label']}")
        print(f"{'='*50}")
        result = analyze_eli5(ex["text"])
        print(f"ציון כולל: {result['total_score']}/100")
        print(f"עובר סף: {'✅' if result['passes_minimum'] else '❌'}")
        print(f"פירוט:")
        for k, v in result["breakdown"].items():
            print(f"  {k}: {v}")
        print(f"משוב: {result['feedback']}")
