"""
Systemic Thinking Test — מבחן חשיבה מערכתית
מעוף Tech-Lead Israel · Score B Component

שרשרת 5 שאלות שכל אחת נובעת מהתשובה הקודמת.
בודק הבנה מערכתית, לא שינון.

Flow:
  1. get_opening_question(topic)          → שאלה פותחת קבועה
  2. get_next_question(topic, qa_pairs)   → Groq מייצר שאלה לפי התשובה
  3. score_chain(topic, qa_pairs)         → ציון סופי לשרשרת

Fallback: שרשראות מוכנות מראש אם Groq לא זמין.
"""

import os
import sys
import json
import time
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from nlp.eli5_analyzer import analyze_eli5, accuracy_score

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
MAX_QUESTIONS = 7  # עד 7 לאדפטיבי

# ──────────────────────────────────────────────
#  שאלות פתיחה — נועדו לחשוף את המודל המנטלי
# ──────────────────────────────────────────────

OPENING_QUESTIONS: Dict[str, Dict] = {
    "סייבר": {
        "question": "מה זה Authentication? הסבר בשפה פשוטה — כאילו לחבר שלא מהתחום.",
        "aspect": "foundation",
    },
    "פייתון": {
        "question": "מה ההבדל בין list לבין dict בפייתון? מתי תבחר כל אחד?",
        "aspect": "foundation",
    },
    "רשתות": {
        "question": "איך בקשה מהדפדפן שלך מגיעה לשרת? תאר את המסלול בשפה פשוטה.",
        "aspect": "foundation",
    },
    "ai": {
        "question": "מה זה overfitting במודל AI? למה זה קורה ומה זה אומר בפועל?",
        "aspect": "foundation",
    },
    "web": {
        "question": "מה קורה כשמשתמש לוחץ Enter אחרי הקלדת URL? פרט את השלבים.",
        "aspect": "foundation",
    },
    "ענן": {
        "question": "מה ההבדל בין שרת פיזי לבין virtual machine? מתי תרצה כל אחד?",
        "aspect": "foundation",
    },
    "מתמטיקה": {
        "question": "מה זה נגזרת? תסביר בדוגמה מחיי יום-יום — לא בנוסחה.",
        "aspect": "foundation",
    },
    "נתונים": {
        "question": "מה ההבדל בין Mean לבין Median? מתי אחד עדיף על השני?",
        "aspect": "foundation",
    },
}

DEFAULT_OPENING = {
    "question": "הסבר את תחום המומחיות שלך — מה הבעיה המרכזית שהתחום פותר ולמה זה חשוב?",
    "aspect": "foundation",
}

# ──────────────────────────────────────────────
#  Fallback chains — כשGroq לא זמין
# ──────────────────────────────────────────────

FALLBACK_CHAINS: Dict[str, List[Dict]] = {
    "סייבר": [
        {"question": "למה הפתרון שתיארת חשוף להתקפת Brute Force? מה המגבלה המהותית?", "aspect": "failure"},
        {"question": "איך 2FA מתמודד עם הבעיה שציינת? מה הוא מוסיף לשכבת האבטחה?", "aspect": "mechanism"},
        {"question": "אם ה-2FA מסתמך על SMS — מה נקודות התורפה? תן דוגמה לתרחיש תקיפה.", "aspect": "connection"},
        {"question": "בהתבסס על כל מה שדיברנו — תכנן auth לאפליקציית בנק. מה תבחר ולמה?", "aspect": "design"},
    ],
    "פייתון": [
        {"question": "מה קורה לביצועים כשאתה מחפש ערך ב-list גדול לעומת dict? למה?", "aspect": "mechanism"},
        {"question": "נניח שאתה בונה מנוע חיפוש — מה ה-data structure שתבחר ולמה?", "aspect": "connection"},
        {"question": "מה הבעיה עם הפתרון שתיארת אם הנתונים לא נכנסים לזיכרון?", "aspect": "failure"},
        {"question": "איך generator יכול לפתור את הבעיה? הסבר את ההבדל בגישה.", "aspect": "design"},
    ],
    "רשתות": [
        {"question": "מה קורה אם ה-DNS server לא זמין? מה משתבש בתהליך שתיארת?", "aspect": "failure"},
        {"question": "מה ההבדל בין HTTP לבין HTTPS בתהליך שתיארת? מה נוסף?", "aspect": "mechanism"},
        {"question": "איך CDN משנה את המסלול שתיארת? מה הוא חוסך?", "aspect": "connection"},
        {"question": "תכנן את ה-infrastructure לאתר שמקבל מיליון בקשות ביום — מה תוסיף?", "aspect": "design"},
    ],
    "ai": [
        {"question": "מה ההבדל בין overfitting לבין underfitting? מה הגורם לכל אחד?", "aspect": "mechanism"},
        {"question": "איך train/validation/test split עוזר לזהות את הבעיה שציינת?", "aspect": "connection"},
        {"question": "מה קורה אם ה-test set דומה מאוד ל-train set? מה זה אומר על הביצועים?", "aspect": "failure"},
        {"question": "תכנן pipeline לאימון מודל לזיהוי תמונות — מה הצעדים ואיפה הסיכונים?", "aspect": "design"},
    ],
}

DEFAULT_FALLBACK = [
    {"question": "מה הגבול של הגישה שתיארת? איפה היא נכשלת?", "aspect": "failure"},
    {"question": "איך הגורם שציינת מתחבר לשאר המערכת? מה ההשפעה הרחבה יותר?", "aspect": "connection"},
    {"question": "מה הפתרון הטוב ביותר לבעיה שזיהית? מה ה-tradeoffs?", "aspect": "design"},
    {"question": "תכנן מערכת מינימלית שמדגימה את כל מה שדיברנו. מה הרכיבים?", "aspect": "design"},
]


# ──────────────────────────────────────────────
#  Groq — יצירת שאלת המשך
# ──────────────────────────────────────────────

_NEXT_Q_SYSTEM = (
    "You are conducting a systemic thinking assessment for a tech candidate. "
    "Your job is to generate ONE follow-up question that digs deeper into their understanding.\n\n"
    "Rules:\n"
    "1. Reference something SPECIFIC the candidate said in their last answer.\n"
    "2. Push one level deeper: ask about WHY it works, WHERE it breaks, HOW it connects, or ask them to DESIGN something.\n"
    "3. The question must be answerable in 3-6 sentences — not trivially yes/no.\n"
    "4. Do not repeat a concept already fully covered.\n"
    "5. Progress through: foundation → mechanism → failure → connection → design.\n\n"
    'Return ONLY valid JSON: {"question": "...", "aspect": "mechanism|failure|connection|design"}'
)


def _format_qa(qa_pairs: List[Dict]) -> str:
    lines = []
    for i, qa in enumerate(qa_pairs, 1):
        lines.append(f"Q{i}: {qa['question']}")
        lines.append(f"A{i}: {qa['answer']}\n")
    return "\n".join(lines)


def _call_groq_next_question(topic: str, qa_pairs: List[Dict]) -> Optional[Dict]:
    if not GROQ_API_KEY or not qa_pairs:
        return None
    try:
        import httpx
        user_msg = (
            f"Topic: {topic}\n\n"
            f"Conversation so far:\n{_format_qa(qa_pairs)}\n"
            f"Generate question #{len(qa_pairs) + 1}."
        )
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": _NEXT_Q_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
            "max_tokens": 150,
            "temperature": 0.4,
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
        if "question" not in parsed:
            return None
        return {
            "question": parsed["question"],
            "aspect":   parsed.get("aspect", "connection"),
            "source":   "groq",
        }
    except Exception:
        return None


# ──────────────────────────────────────────────
#  Public API
# ──────────────────────────────────────────────

def get_opening_question(topic: str) -> Dict:
    """מחזיר שאלת פתיחה לפי נושא."""
    topic_norm = topic.strip().lower()
    for key, val in OPENING_QUESTIONS.items():
        if key in topic_norm or topic_norm in key:
            return {"question": val["question"], "aspect": val["aspect"],
                    "question_index": 1, "source": "predefined"}
    return {**DEFAULT_OPENING, "question_index": 1, "source": "predefined"}


def get_next_question(topic: str, qa_pairs: List[Dict]) -> Dict:
    """
    מחזיר שאלת המשך.
    מנסה Groq קודם, fallback לשרשרת מוכנה.

    qa_pairs: [{"question": "...", "answer": "..."}, ...]
    """
    question_index = len(qa_pairs) + 1

    if question_index > MAX_QUESTIONS:
        return {"done": True, "question_index": question_index}

    # נסה Groq
    groq_result = _call_groq_next_question(topic, qa_pairs)
    if groq_result:
        return {**groq_result, "question_index": question_index}

    # Fallback
    fallback = _get_fallback_question(topic, len(qa_pairs) - 1)
    return {**fallback, "question_index": question_index, "source": "fallback"}


def _get_fallback_question(topic: str, chain_index: int) -> Dict:
    topic_norm = topic.strip().lower()
    for key, chain in FALLBACK_CHAINS.items():
        if key in topic_norm or topic_norm in key:
            if chain_index < len(chain):
                return chain[chain_index]
    if chain_index < len(DEFAULT_FALLBACK):
        return DEFAULT_FALLBACK[chain_index]
    return {"question": "סכם את מה שלמדת — מה הנקודה המרכזית שאתה לוקח מהשיחה הזו?",
            "aspect": "design"}


# ──────────────────────────────────────────────
#  Scoring
# ──────────────────────────────────────────────

def score_chain(topic: str, qa_pairs: List[Dict]) -> Dict:
    """
    ציון סופי לשרשרת.

    per_answer:      ניתוח ELI5 לכל תשובה
    depth_score:     האם התשובות מעמיקות עם הזמן?
    coverage_score:  כיסוי מושגי ליבה לאורך כל השרשרת
    consistency:     האם אין סתירות? (TTR גבוה = התקדמות)
    total_score:     משוקלל
    """
    if not qa_pairs:
        return {"total_score": 0.0, "error": "no answers"}

    answers = [qa["answer"] for qa in qa_pairs]

    # --- ניתוח ELI5 לכל תשובה ---
    per_answer = []
    for i, ans in enumerate(answers):
        a = analyze_eli5(ans, topic=topic)
        per_answer.append({
            "index": i + 1,
            "score": a["total_score"],
            "accuracy": a["breakdown"].get("accuracy", 50),
            "coherence": a["breakdown"].get("coherence", 50),
        })

    scores = [p["score"] for p in per_answer]
    avg_score = sum(scores) / len(scores)

    # --- depth_score: האם התשובות מעמיקות? ---
    # בודקים אם חצי שני > חצי ראשון
    mid = len(scores) // 2
    first_half  = sum(scores[:mid])  / max(mid, 1)
    second_half = sum(scores[mid:])  / max(len(scores) - mid, 1)
    depth_score = min(100.0, max(0.0, 50 + (second_half - first_half) * 2))

    # --- coverage_score: כיסוי מושגי ליבה בכל השרשרת ---
    full_text = " ".join(answers)
    coverage_score = accuracy_score(full_text, topic)

    # --- consistency: TTR גבוה = מגוון = התקדמות אמיתית ---
    from nlp.eli5_analyzer import tokenize
    all_words = tokenize(full_text)
    if len(all_words) > 10:
        ttr = len(set(w.lower() for w in all_words)) / len(all_words)
        consistency = min(100.0, ttr * 130)
    else:
        consistency = 50.0

    # --- answer length progression ---
    lengths = [len(a.split()) for a in answers]
    avg_len = sum(lengths) / len(lengths)
    length_score = min(100.0, avg_len * 2.5)  # 40 מילים בממוצע = 100

    total = round(
        avg_score      * 0.35 +
        depth_score    * 0.25 +
        coverage_score * 0.20 +
        consistency    * 0.10 +
        length_score   * 0.10,
        2,
    )

    return {
        "total_score":     total,
        "passes_minimum":  total >= 55,
        "avg_answer_score": round(avg_score, 2),
        "depth_score":     round(depth_score, 2),
        "coverage_score":  round(coverage_score, 2),
        "consistency":     round(consistency, 2),
        "length_score":    round(length_score, 2),
        "per_answer":      per_answer,
        "questions_answered": len(qa_pairs),
    }


# ──────────────────────────────────────────────
#  CLI demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    topic = "סייבר"
    print(f"=== Systemic Thinking Test — {topic} ===\n")

    qa_pairs = []
    q = get_opening_question(topic)
    print(f"Q1 [{q['aspect']}]: {q['question']}\n")

    # סימולציה של תשובות
    demo_answers = [
        "Authentication זה תהליך שבו מערכת מוודאת שאתה מי שאתה אומר שאתה. "
        "כמו מנעול על הדלת — אתה צריך מפתח כדי להיכנס. הסיסמה היא המפתח.",
        "אם מישהו מנסה הרבה סיסמאות שונות הוא בסוף ימצא את הנכונה. "
        "אין גבול על מספר הניסיונות — זו הבעיה המרכזית.",
        "2FA מוסיף שכבה שנייה — גם אם ידעת את הסיסמה, צריך גם קוד מהטלפון. "
        "כמו שיש מנעול וגם שומר בדלת.",
        "אם ה-SMS מיירטו — למשל SIM swap — אפשר לקבל את הקוד. "
        "זו חולשה שטלקום חברות לא תמיד מגנות עליה.",
        "לבנק אני אבחר TOTP app כמו Google Authenticator, לא SMS. "
        "בנוסף — rate limiting על ניסיונות כניסה, ו-hardware key לאנשי מפתח.",
    ]

    for i, ans in enumerate(demo_answers):
        qa_pairs.append({"question": q["question"], "answer": ans})
        print(f"A{i+1}: {ans[:80]}...\n")

        next_q = get_next_question(topic, qa_pairs)
        if next_q.get("done"):
            break
        q = next_q
        print(f"Q{i+2} [{q['aspect']}] (source={q.get('source','?')}): {q['question']}\n")

    result = score_chain(topic, qa_pairs)
    print(f"\n{'='*50}")
    print(f"ציון סופי:    {result['total_score']}/100")
    print(f"עובר סף:      {'✅' if result['passes_minimum'] else '❌'}")
    print(f"עומק:         {result['depth_score']}")
    print(f"כיסוי מושגים: {result['coverage_score']}")
    print(f"עקביות:       {result['consistency']}")
    print(f"שאלות שנענו:  {result['questions_answered']}")
