"""
Code Test — מבחן טכני אדפטיבי
מעוף Tech-Lead Israel

מבחן קוד בשלושה חלקים:
  חלק 1 — שאלון אדפטיבי (שאלות תיאורטיות מתקדמות)
  חלק 2 — הסבר קוד (ELI5 טכני)
  חלק 3 — ניתוח בעיה (שאלה פתוחה)

עובד ללא sandbox — מבוסס תשובות טקסט.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import List, Dict, Optional
from nlp.eli5_analyzer import analyze_eli5

# --- שאלות אדפטיביות לפי Tech Stack ורמה ---

ADAPTIVE_QUESTIONS = {
    "python": [
        {
            "level": 1,
            "question": "מה ההבדל בין list לבין tuple בפייתון? מתי תעדיף כל אחד?",
            "keywords": ["list", "tuple", "mutable", "immutable", "שינוי", "קבוע", "מהירות"],
            "expected_concepts": ["שינוי", "אורך", "ביצועים"],
        },
        {
            "level": 2,
            "question": "הסבר מה זה decorator בפייתון ותן דוגמה לשימוש מעשי.",
            "keywords": ["decorator", "@", "wrapper", "function", "פונקציה", "עטיפה"],
            "expected_concepts": ["עטיפה", "הוספת פונקציונליות", "logging"],
        },
        {
            "level": 3,
            "question": "מה זה generator ולמה הוא חוסך זיכרון? תן דוגמה.",
            "keywords": ["generator", "yield", "lazy", "memory", "זיכרון", "איטרטור"],
            "expected_concepts": ["yield", "זיכרון", "עצלני"],
        },
        {
            "level": 4,
            "question": "הסבר את מושג ה-GIL בפייתון ומה השפעתו על multithreading.",
            "keywords": ["gil", "global interpreter lock", "thread", "multiprocessing", "concurrent"],
            "expected_concepts": ["נעילה", "thread", "מקבילות"],
        },
        {
            "level": 5,
            "question": "תכנן מערכת caching פשוטה בפייתון. מה ה-data structure שתבחר ולמה?",
            "keywords": ["cache", "dict", "lru", "ttl", "hash", "מפתח"],
            "expected_concepts": ["מילון", "TTL", "LRU", "ביצועים"],
        },
    ],
    "cyber": [
        {
            "level": 1,
            "question": "מה ההבדל בין Authentication לבין Authorization? תן דוגמה לכל אחד.",
            "keywords": ["authentication", "authorization", "זהות", "הרשאה", "token", "password"],
            "expected_concepts": ["זהות", "הרשאה", "הבדל"],
        },
        {
            "level": 2,
            "question": "הסבר מהי SQL Injection ואיך מונעים אותה.",
            "keywords": ["sql injection", "input", "sanitize", "prepared statement", "escape", "query"],
            "expected_concepts": ["קלט זדוני", "מניעה", "prepared"],
        },
        {
            "level": 3,
            "question": "מה זה Man-in-the-Middle attack? תאר תרחיש מציאותי.",
            "keywords": ["mitm", "interception", "https", "certificate", "wifi", "ציתות"],
            "expected_concepts": ["יירוט", "תקשורת", "הצפנה"],
        },
        {
            "level": 4,
            "question": "הסבר את ההבדל בין symmetric לבין asymmetric encryption. מתי משתמשים בכל אחד?",
            "keywords": ["symmetric", "asymmetric", "aes", "rsa", "public key", "private key", "מפתח"],
            "expected_concepts": ["מפתח ציבורי", "מפתח פרטי", "מהירות"],
        },
        {
            "level": 5,
            "question": "תכנן את האדריכלות האבטחתית של אפליקציית בנקאות. מה 5 השכבות שתוסיף?",
            "keywords": ["authentication", "encryption", "firewall", "audit", "2fa", "zero trust"],
            "expected_concepts": ["הצפנה", "אימות", "ניטור", "הרשאות"],
        },
    ],
    "data": [
        {
            "level": 1,
            "question": "מה ההבדל בין mean, median ו-mode? מתי כל אחד מועיל יותר?",
            "keywords": ["mean", "median", "mode", "ממוצע", "חציון", "שכיח", "outlier"],
            "expected_concepts": ["ממוצע", "חציון", "ערכים קיצוניים"],
        },
        {
            "level": 2,
            "question": "מה זה overfitting ואיך מזהים ותיקנים אותו?",
            "keywords": ["overfitting", "train", "test", "validation", "regularization", "dropout"],
            "expected_concepts": ["אימון", "בדיקה", "הכללה"],
        },
        {
            "level": 3,
            "question": "הסבר את ההבדל בין supervised לבין unsupervised learning. תן דוגמה לכל אחד.",
            "keywords": ["supervised", "unsupervised", "label", "cluster", "classification", "kmeans"],
            "expected_concepts": ["תוויות", "קיבוץ", "סיווג"],
        },
        {
            "level": 4,
            "question": "מה זה feature engineering ולמה זה חשוב יותר לרוב מהמודל עצמו?",
            "keywords": ["feature", "engineering", "normalization", "encoding", "selection", "importance"],
            "expected_concepts": ["עיצוב מאפיינים", "חשיבות", "איכות נתונים"],
        },
        {
            "level": 5,
            "question": "תכנן pipeline לאנליזה של 10 מיליון רשומות. מה הכלים ואיך תתמודד עם הנפח?",
            "keywords": ["pipeline", "spark", "dask", "batch", "streaming", "distributed", "partitioning"],
            "expected_concepts": ["עיבוד מבוזר", "batch", "ביצועים"],
        },
    ],
    "default": [
        {
            "level": 1,
            "question": "הסבר מהי בעיה טכנית שפתרת בצבא — מה הבעיה, מה הפתרון, מה למדת?",
            "keywords": ["בעיה", "פתרון", "למדתי", "אנליזה", "שיפור"],
            "expected_concepts": ["בעיה", "פתרון", "לקח"],
        },
        {
            "level": 2,
            "question": "אם היית צריך ללמד מישהו בצוות שלך משימה טכנית חדשה, איך היית עושה את זה?",
            "keywords": ["הדרכה", "הסבר", "תרגול", "שאלות", "feedback"],
            "expected_concepts": ["הדרכה", "תרגול", "הפשטה"],
        },
        {
            "level": 3,
            "question": "תאר מצב שבו הייתה לך מחלוקת טכנית עם עמית. איך פתרת אותה?",
            "keywords": ["מחלוקת", "פשרה", "הוכחה", "נתונים", "שיתוף פעולה"],
            "expected_concepts": ["ועדה", "נתונים", "פשרה"],
        },
        {
            "level": 4,
            "question": "אם יש לך שעה לשיפור מערכת קיימת, על מה תתמקד קודם ולמה?",
            "keywords": ["עדיפות", "ביצועים", "bottleneck", "מדידה", "השפעה"],
            "expected_concepts": ["עדיפות", "מדידה", "השפעה"],
        },
        {
            "level": 5,
            "question": "תכנן בגדול מערכת לניהול 1000 משתמשים — ארכיטקטורה, DB, API.",
            "keywords": ["ארכיטקטורה", "database", "api", "scaling", "cache", "security"],
            "expected_concepts": ["ארכיטקטורה", "שכבות", "אבטחה"],
        },
    ],
}

LEVEL_SCORES = {1: 30, 2: 55, 3: 70, 4: 85, 5: 100}
PASS_THRESHOLD = 50


def _detect_stack(tech_stack: List[str]) -> str:
    """זיהוי תחום מה-Tech Stack"""
    stack_lower = [t.lower() for t in tech_stack]
    if any(t in stack_lower for t in ["python", "py", "פייתון", "django", "flask"]):
        return "python"
    if any(t in stack_lower for t in ["cyber", "סייבר", "security", "אבטחה", "network"]):
        return "cyber"
    if any(t in stack_lower for t in ["data", "ml", "machine learning", "ai", "נתונים", "analytics"]):
        return "data"
    return "default"


def _score_answer(answer: str, question: Dict) -> float:
    """
    מחשב ציון לתשובה טכנית:
    - ELI5 quality (50%)
    - כיסוי מושגים מצופים (50%)
    """
    eli5 = analyze_eli5(answer)
    eli5_score = eli5["total_score"]

    # בדיקת כיסוי מושגים
    answer_lower = answer.lower()
    keywords_found = sum(
        1 for kw in question.get("keywords", [])
        if kw.lower() in answer_lower
    )
    keyword_coverage = min(100.0, (keywords_found / max(1, len(question["keywords"]))) * 150)

    return round(eli5_score * 0.50 + keyword_coverage * 0.50, 2)


def run_code_test(
    answers: List[str],
    tech_stack: Optional[List[str]] = None,
) -> Dict:
    """
    מריץ מבחן קוד אדפטיבי.

    קלט:
      answers    — תשובות המועמד לפי סדר
      tech_stack — רשימת טכנולוגיות (לבחירת שאלות מתאימות)

    פלט:
      final_level, adaptive_score, passed, results, summary
    """
    stack = tech_stack or []
    domain = _detect_stack(stack)
    questions = ADAPTIVE_QUESTIONS[domain]

    results = []
    current_level = 0

    for i, answer in enumerate(answers):
        if i >= len(questions):
            break

        q = questions[i]
        score = _score_answer(answer, q)

        results.append({
            "level": q["level"],
            "question": q["question"],
            "answer_score": round(score, 1),
            "passes": score >= PASS_THRESHOLD,
            "keywords_expected": q["keywords"][:4],
        })

        current_level = q["level"]

        if score < PASS_THRESHOLD:
            break

    if not results:
        return {
            "domain": domain,
            "questions_asked": 0,
            "final_level": 0,
            "adaptive_score": 0.0,
            "passed": False,
            "results": [],
            "summary": "לא נענו שאלות",
        }

    final_level = current_level
    base_score = LEVEL_SCORES.get(final_level, 0)
    avg_quality = sum(r["answer_score"] for r in results) / len(results)
    adaptive_score = round(base_score * 0.70 + avg_quality * 0.30, 2)
    adaptive_score = min(100.0, adaptive_score)

    last = results[-1]
    if last["passes"] and len(results) == len(questions):
        summary = f"השלים את כל 5 הרמות בתחום {domain} — ציון מקסימלי!"
    elif last["passes"]:
        summary = f"הגיע לרמה {final_level}/5 ועבר — ממשיך לשאלה הבאה."
    else:
        summary = f"עצר ברמה {final_level}/5 — תשובה לא עברה סף ({last['answer_score']:.0f}/100)."

    return {
        "domain": domain,
        "questions_asked": len(results),
        "final_level": final_level,
        "max_level": len(questions),
        "adaptive_score": adaptive_score,
        "avg_quality": round(avg_quality, 2),
        "passed": adaptive_score >= 60,
        "results": results,
        "summary": summary,
        "next_question": (
            questions[len(results)]["question"]
            if len(results) < len(questions) and last["passes"]
            else None
        ),
    }


def get_first_question(tech_stack: Optional[List[str]] = None) -> Dict:
    """מחזיר את השאלה הראשונה לפי Tech Stack"""
    domain = _detect_stack(tech_stack or [])
    q = ADAPTIVE_QUESTIONS[domain][0]
    return {
        "domain": domain,
        "level": q["level"],
        "question": q["question"],
        "hint": "ענה בצורה מפורטת — נסה להסביר כאילו לאדם שלא בתחום",
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Code Test — Demo")
    print("=" * 55)

    good_answers = [
        "ההבדל המרכזי: list ניתן לשינוי (mutable) ו-tuple לא. כשאני יודע שהנתונים לא ישתנו — אבחר tuple כי הוא מהיר יותר בגישה ומוגן מטעויות. לדוגמה: קואורדינטות GPS = tuple. רשימת משתמשים = list.",
        "decorator זה כמו עטיפה סביב פונקציה. הוא מוסיף פונקציונליות בלי לשנות את הקוד המקורי. דוגמה: @login_required בDjango — בודק שהמשתמש מחובר לפני כל endpoint.",
        "generator מחשב ערכים רק כשצריך אותם — לא טוען הכל לזיכרון. במקום list של מיליון פריטים שתופסים 1GB, generator מחזיר אחד בכל פעם. שימוש: yield במקום return.",
    ]

    weak_answers = [
        "list ו-tuple שניהם אוסף של אלמנטים בפייתון.",
    ]

    for label, answers, stack in [
        ("מועמד טוב — Python", good_answers, ["Python", "Django"]),
        ("מועמד חלש — עצר בשאלה 1", weak_answers, ["Python"]),
    ]:
        print(f"\n{'─'*55}")
        print(f"  {label}")
        result = run_code_test(answers, stack)
        print(f"  תחום: {result['domain']} | שאלות: {result['questions_asked']}/5 | רמה: {result['final_level']}/5")
        print(f"  ציון: {result['adaptive_score']}/100 | עובר: {result['passed']}")
        print(f"  סיכום: {result['summary']}")
