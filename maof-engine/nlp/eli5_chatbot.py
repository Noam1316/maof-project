"""
ELI5 Chatbot — מבחן אדפטיבי להערכת יכולת הסבר
מעוף Tech-Lead Israel

שלב 3 של מבחן ELI5:
- שאלות מתקדמות בהתאם לביצועים
- כל שאלה קשורה לקודמת
- ציון לפי עד שאלה כמה הגיע + ממוצע ELI5

עובד ללא LLM — שאלות מוכנות מראש לפי נושא.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import List, Dict, Optional
from nlp.eli5_analyzer import analyze_eli5

# --- שאלות אדפטיביות לפי נושא ורמה ---

QUESTION_BANKS = {
    "סייבר": [
        {
            "level": 1,
            "question": "הסבר מהי אבטחת סייבר לילד בכיתה ו' שמעולם לא שמע את המילה הזו.",
            "hint": "השתמש באנלוגיה מחיי יום-יום (בית, מנעול, שמירה...)",
            "min_score": 0,
        },
        {
            "level": 2,
            "question": "הסבר את ההבדל בין וירוס מחשב לבין תוכנת כופר (Ransomware) — בשפה פשוטה.",
            "hint": "דמיין שניהם כגנבים — מה ההבדל בין מה שהם עושים?",
            "min_score": 55,
        },
        {
            "level": 3,
            "question": "למה סיסמה חזקה חשובה? הסבר את ההסתברות של פיצוח בדרך יצירתית.",
            "hint": "אפשר להשתמש בדוגמת קוד כספת...",
            "min_score": 65,
        },
        {
            "level": 4,
            "question": "הסבר איך עובד HTTPS והצפנה לאדם שיודע רק מה זה אינטרנט.",
            "hint": "מעטפה סגורה? שפה סודית? הכל כשיר...",
            "min_score": 72,
        },
        {
            "level": 5,
            "question": "הסבר את עקרון ה-Zero Trust לאדם שמכיר רק את מושג הבנק.",
            "hint": "מדוע 'לא לסמוך על אף אחד' הוא עיקרון אבטחה?",
            "min_score": 80,
        },
    ],
    "פייתון": [
        {
            "level": 1,
            "question": "הסבר מהי שפת תכנות פייתון לסבא שאף פעם לא נגע במחשב.",
            "hint": "מתכון? הוראות? מה שנוח לך...",
            "min_score": 0,
        },
        {
            "level": 2,
            "question": "הסבר מהי לולאה (loop) בתכנות לילד בן 10 בעזרת דוגמה מהחיים.",
            "hint": "מה חוזר על עצמו בחיי יום-יום?",
            "min_score": 55,
        },
        {
            "level": 3,
            "question": "הסבר את ההבדל בין list לבין dictionary בפייתון — בלי מונחים טכניים.",
            "hint": "מה ההבדל בין רשימת קניות למילון עברי-אנגלי?",
            "min_score": 65,
        },
        {
            "level": 4,
            "question": "הסבר מהי פונקציה ולמה משתמשים בה — לאדם שמכיר מתמטיקה בלבד.",
            "hint": "f(x) = ... זה מוכר לו. איך מחברים?",
            "min_score": 72,
        },
        {
            "level": 5,
            "question": "הסבר מהו API ואיך פייתון מתקשר עם שירותי אינטרנט — לאדם שמשתמש בסמארטפון.",
            "hint": "מסעדה? שפה משותפת? גשר?",
            "min_score": 80,
        },
    ],
    "מתמטיקה": [
        {
            "level": 1,
            "question": "הסבר מה זה אחוזים לילד בכיתה ד' שיודע חיבור וחיסור.",
            "hint": "פיצה? כסף? מה שנוח לך...",
            "min_score": 0,
        },
        {
            "level": 2,
            "question": "הסבר מהי הסתברות לאדם שאוהב לשחק קלפים.",
            "hint": "קוביה? הגרלה? חישוב סיכויים...",
            "min_score": 55,
        },
        {
            "level": 3,
            "question": "הסבר מה זה גרף ומה הוא מראה לנו — בלי מונחי מתמטיקה.",
            "hint": "תמונה של מידע? סיפור חזותי?",
            "min_score": 65,
        },
        {
            "level": 4,
            "question": "הסבר את מושג הנגזרת לאדם שנוהג ברכב.",
            "hint": "מד המהירות מראה... בדיוק מה?",
            "min_score": 72,
        },
        {
            "level": 5,
            "question": "הסבר מה זה אלגוריתם ולמה מתמטיקה היא הבסיס שלו — לאדם בן 15.",
            "hint": "מתכון? הוראות שלב אחר שלב? הכל חוקי...",
            "min_score": 80,
        },
    ],
    "default": [
        {
            "level": 1,
            "question": "הסבר את הנושא שלמדת הכי טוב בצבא לאדם שאין לו רקע טכני.",
            "hint": "תחשוב על מישהו קרוב שאין לו מושג — איך תסביר?",
            "min_score": 0,
        },
        {
            "level": 2,
            "question": "תן דוגמה מחיי יום-יום שממחישה את אותו עיקרון שהסברת.",
            "hint": "ככל שהדוגמה יצירתית יותר — כך טוב יותר",
            "min_score": 55,
        },
        {
            "level": 3,
            "question": "עכשיו הסבר את אותו נושא לילד בן 8. מה שונה בהסבר?",
            "hint": "פחות מילים, יותר אנלוגיות...",
            "min_score": 65,
        },
        {
            "level": 4,
            "question": "מה היה הרגע שבו הנושא הזה 'קליק' לך? הסבר אותו רגע.",
            "hint": "הרגע ה-'אהה!' — מה גרם לך להבין?",
            "min_score": 72,
        },
        {
            "level": 5,
            "question": "אם היית מלמד את הנושא הזה בכיתה י', מה שיטת ההוראה שלך?",
            "hint": "מה ייחודי בגישה שלך?",
            "min_score": 80,
        },
    ],
}

# ניקוד לפי עד שאלה כמה הגיע
LEVEL_SCORES = {1: 30, 2: 55, 3: 72, 4: 85, 5: 100}
PASS_THRESHOLD = 55  # מינימום לשאלה הבאה


def get_questions(topic: str) -> List[Dict]:
    """מחזיר שאלות לנושא — עם fallback ל-default"""
    topic_lower = topic.lower()
    for key in QUESTION_BANKS:
        if key in topic_lower:
            return QUESTION_BANKS[key]
    return QUESTION_BANKS["default"]


def run_adaptive_session(
    topic: str,
    answers: List[str],
) -> Dict:
    """
    מנתח תשובות למבחן אדפטיבי.

    קלט:
      topic   — נושא המבחן (סייבר, פייתון...)
      answers — רשימת תשובות לפי סדר השאלות

    פלט:
      questions_asked, scores_per_answer, final_level,
      adaptive_score, passed, feedback
    """
    questions = get_questions(topic)
    results = []
    current_level = 0

    for i, answer in enumerate(answers):
        if i >= len(questions):
            break

        q = questions[i]
        analysis = analyze_eli5(answer)
        score = analysis["total_score"]

        results.append({
            "level": q["level"],
            "question": q["question"],
            "answer_score": round(score, 1),
            "passes": score >= PASS_THRESHOLD,
            "feedback": analysis["feedback"],
        })

        current_level = q["level"]

        # בדוק אם להמשיך לשאלה הבאה
        if score < PASS_THRESHOLD:
            break  # עצור — לא מספיק טוב לשאלה הבאה

    # ציון סופי
    if not results:
        return {
            "questions_asked": 0,
            "final_level": 0,
            "adaptive_score": 0.0,
            "passed": False,
            "results": [],
            "summary": "לא נענו שאלות",
        }

    final_level = current_level
    base_score = LEVEL_SCORES.get(final_level, 0)

    # ממוצע איכות התשובות שנענו
    avg_quality = sum(r["answer_score"] for r in results) / len(results)

    # ציון משולב: מה הגיע (70%) + איכות תשובות (30%)
    adaptive_score = round(base_score * 0.70 + avg_quality * 0.30, 2)
    adaptive_score = min(100.0, adaptive_score)

    last_result = results[-1]
    if last_result["passes"]:
        summary = f"הגיע לרמה {final_level}/5 — מצוין! כל התשובות עברו את הסף."
    else:
        summary = f"עצר ברמה {final_level}/5 — תשובה לא עברה סף ({last_result['answer_score']:.0f}/100)."

    return {
        "topic": topic,
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
            if len(results) < len(questions) and last_result["passes"]
            else None
        ),
    }


def get_next_question(topic: str, level: int) -> Optional[Dict]:
    """מחזיר את השאלה הבאה לפי רמה"""
    questions = get_questions(topic)
    next_level = level  # 0-indexed
    if next_level < len(questions):
        q = questions[next_level]
        return {
            "level": q["level"],
            "question": q["question"],
            "hint": q["hint"],
        }
    return None


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("ELI5 Chatbot — Demo")
    print("=" * 55)

    # סימולציה: מועמד עם תשובות מגוונות
    answers_good = [
        "סייבר זה כמו מנעול על הדלת של המחשב שלך. דמיין שהמחשב הוא בית — אנשי הסייבר שומרים שאף אחד לא יכנס.",
        "וירוס זה כמו מחלה שמתפשטת — הוא נדבק לקבצים. כופרה זה שונה — כמו גנב שנועל לך את הבית ודורש כסף פדיון.",
        "סיסמה חזקה זה כמו קוד כספת — ככל שיש יותר ספרות ותווים שונים, קשה יותר לפצח. סיסמה של 4 ספרות = 10,000 אפשרויות. של 12 תווים = מיליארדים.",
    ]

    answers_weak = [
        "סייבר זה אבטחת מידע ומניעת חדירות למערכות מחשוב ארגוניות באמצעות פרוטוקולי הגנה.",
    ]

    for label, answers, topic in [
        ("מועמד טוב (3 תשובות)", answers_good, "סייבר"),
        ("מועמד חלש (עצר בשאלה 1)", answers_weak, "סייבר"),
    ]:
        print(f"\n{'─'*55}")
        print(f"  {label}")
        result = run_adaptive_session(topic, answers)
        print(f"  שאלות: {result['questions_asked']}/5 | רמה: {result['final_level']}/5")
        print(f"  ציון אדפטיבי: {result['adaptive_score']}/100")
        print(f"  עובר: {result['passed']}")
        print(f"  סיכום: {result['summary']}")
