"""
Logic Test — מבחן הגיון בשפה זרה (Layer 1)
מעוף Tech-Lead Israel · Growth Potential component

הרעיון: מציגים קוד בשפה מומצאת שאיש לא מכיר, עם החוקים נתונים inline.
המועמד לא נבדק על ידע קודם — אלא על מהירות הסקה והעברת חשיבה.

Flow:
  1. get_logic_question(level)              → שאלה (קוד + חוקים, בלי התשובה)
  2. score_logic_answer(question_id, answer)→ Groq מדרג לפי רובריקה + fallback

מדורג open-ended: המועמד מסביר במילים מה הקוד עושה / מה הפלט.
Groq בודק נכונות הפלט + איכות ההסקה (לא דמיון לטקסט).
"""

import os
import sys
import json
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"


# ──────────────────────────────────────────────
#  Question bank — invented languages, rules inline
#  Each: rules given so it is PURE reasoning, not recall.
#  `answer` + `key_steps` are used for grading only (never sent to client).
# ──────────────────────────────────────────────

QUESTIONS: List[Dict] = [
    {
        "id": "LOGIC_STK_1",
        "level": 1,
        "language": "STK",
        "rules": (
            "בשפת STK המספרים נדחפים למחסנית (stack):\n"
            "• מספר  → נדחף לראש המחסנית\n"
            "• +     → מוציא שני מספרים ודוחף את הסכום\n"
            "• *     → מוציא שני מספרים ודוחף את המכפלה\n"
            "• .     → מדפיס את המספר שבראש המחסנית"
        ),
        "code": "5 3 + 2 * .",
        "prompt": "מה יודפס? הסבר שלב-אחר-שלב איך הגעת לתשובה.",
        "answer": "16",
        "key_steps": "דחיפת 5 ו-3, חיבור ל-8, דחיפת 2, מכפלה 8*2=16, הדפסת 16",
    },
    {
        "id": "LOGIC_LMD_2",
        "level": 2,
        "language": "LMD",
        "rules": (
            "בשפת LMD עובדים על רשימות:\n"
            "• [a b c] → רשימה\n"
            "• ^       → הופך את סדר הרשימה\n"
            "• #       → מחזיר את אורך הרשימה\n"
            "• @n      → מחזיר את האיבר ה-n (החל מ-1)"
        ),
        "code": "[7 4 9 2] ^ @2",
        "prompt": "מה התוצאה? הסבר את הצעדים.",
        "answer": "9",
        "key_steps": "היפוך הרשימה ל-[2 9 4 7], לקיחת האיבר השני = 9",
    },
    {
        "id": "LOGIC_LOOP_3",
        "level": 3,
        "language": "LOOP",
        "rules": (
            "בשפת LOOP:\n"
            "• acc=1        → מאתחל משתנה acc לערך 1\n"
            "• rep n { … }  → חוזר על הפעולות בסוגריים n פעמים\n"
            "• acc*=2       → מכפיל את acc ב-2\n"
            "• print acc    → מדפיס את acc"
        ),
        "code": "acc=1; rep 5 { acc*=2 }; print acc",
        "prompt": "מה יודפס? הסבר את ההיגיון — לא רק את המספר.",
        "answer": "32",
        "key_steps": "הכפלה ב-2 חמש פעמים: 1→2→4→8→16→32, כלומר 2 בחזקת 5 = 32",
    },
]

_BY_ID = {q["id"]: q for q in QUESTIONS}


# ──────────────────────────────────────────────
#  Public — get question (without the answer)
# ──────────────────────────────────────────────

def get_logic_question(level: int = 1) -> Dict:
    """מחזיר שאלת הגיון לפי רמה (1-3). ללא התשובה."""
    level = max(1, min(3, int(level)))
    q = next((x for x in QUESTIONS if x["level"] == level), QUESTIONS[0])
    return {
        "id":       q["id"],
        "level":    q["level"],
        "language": q["language"],
        "rules":    q["rules"],
        "code":     q["code"],
        "prompt":   q["prompt"],
    }


# ──────────────────────────────────────────────
#  Groq — rubric grading (correctness + reasoning)
# ──────────────────────────────────────────────

_LOGIC_SYSTEM = (
    "You are assessing a candidate's raw logical reasoning in a timed test. "
    "They were shown code in an INVENTED language (rules were provided to them) and asked "
    "to determine the output and explain their reasoning step by step.\n\n"
    "You are given the CORRECT output and the key reasoning steps. Grade fairly on TWO dimensions:\n"
    "  correctness (0-100): Did they reach the correct final output? "
    "Give strong partial credit for the right method with a small arithmetic slip.\n"
    "  reasoning (0-100): Did they show a genuine step-by-step trace of the logic, "
    "not just guess a number? Reward correct tracing even if phrased differently.\n\n"
    "Do NOT reward verbosity or similarity to any reference wording — reward correct logic only.\n"
    'Return ONLY valid JSON: {"correctness": N, "reasoning": N, "feedback": "one short sentence in Hebrew"}'
)


def _call_groq_logic(q: Dict, answer: str) -> Optional[Dict]:
    if not GROQ_API_KEY or not answer.strip():
        return None
    try:
        import httpx
        user_msg = (
            f"Language: {q['language']}\n"
            f"Rules:\n{q['rules']}\n\n"
            f"Code:\n{q['code']}\n\n"
            f"CORRECT output: {q['answer']}\n"
            f"Key reasoning steps: {q['key_steps']}\n\n"
            f"Candidate's answer:\n{answer[:1200]}"
        )
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": _LOGIC_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
            "max_tokens": 120,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        resp = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=8.0,
        )
        if resp.status_code != 200:
            return None
        parsed = json.loads(resp.json()["choices"][0]["message"]["content"])
        if "correctness" not in parsed or "reasoning" not in parsed:
            return None
        c = max(0.0, min(100.0, float(parsed["correctness"])))
        r = max(0.0, min(100.0, float(parsed["reasoning"])))
        return {
            "correctness": c,
            "reasoning":   r,
            "composite":   round(c * 0.6 + r * 0.4, 2),
            "feedback":    parsed.get("feedback", ""),
        }
    except Exception:
        return None


def _heuristic_logic(q: Dict, answer: str) -> Dict:
    """Fallback — בודק אם הפלט הנכון מופיע + האם יש סימני הסקה (שלבים)."""
    text = answer.strip().lower()
    correct = str(q["answer"]).lower()

    has_output = correct in text.replace(",", "").replace(".", " ")
    # סימני הסקה — מספרים מרובים / מילות שלב
    step_markers = ["->", "→", "אז", "ואז", "שלב", "קודם", "אחר כך", "=", "כי"]
    shows_steps = sum(1 for m in step_markers if m in text) >= 2 or len([t for t in text.split() if t.isdigit()]) >= 3

    if has_output and shows_steps:
        score = 85.0
    elif has_output:
        score = 70.0
    elif shows_steps:
        score = 40.0
    else:
        score = 20.0

    return {
        "score":    score,
        "method":   "heuristic",
        "feedback": "ניתוח מבני — Groq לא זמין" if not has_output else "פלט נכון זוהה",
    }


def score_logic_answer(question_id: str, answer: str) -> Dict:
    """
    מדרג תשובת הגיון.
    מנסה Groq (correctness + reasoning, רובריקה); fallback — היוריסטיקה.
    """
    q = _BY_ID.get(question_id)
    if not q:
        return {"score": 0.0, "error": f"שאלה לא נמצאה: {question_id}"}

    groq = _call_groq_logic(q, answer)
    if groq:
        return {
            "score":       groq["composite"],
            "correctness": groq["correctness"],
            "reasoning":   groq["reasoning"],
            "feedback":    groq.get("feedback", ""),
            "passes":      groq["composite"] >= 55,
            "method":      "groq",
        }

    h = _heuristic_logic(q, answer)
    return {
        "score":    h["score"],
        "feedback": h["feedback"],
        "passes":   h["score"] >= 55,
        "method":   h["method"],
    }


# ──────────────────────────────────────────────
#  CLI demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for lvl in (1, 2, 3):
        q = get_logic_question(lvl)
        print(f"\n=== Level {lvl} — {q['language']} ===")
        print(q["rules"])
        print(f"\nCode: {q['code']}")
        print(q["prompt"])
        # simulate a correct answer
        full = _BY_ID[q["id"]]
        demo = f"הפלט הוא {full['answer']}. {full['key_steps']}"
        res = score_logic_answer(q["id"], demo)
        print(f"→ demo answer scored: {res['score']} ({res['method']})")
