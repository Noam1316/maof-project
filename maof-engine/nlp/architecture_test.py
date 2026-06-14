"""
Architecture Test — תכנון מערכת בלי קוד (Layer 3)
מעוף Tech-Lead Israel · Systemic Thinking component

הרעיון: המועמד מתאר תוכנית פעולה / ארכיטקטורה למערכת — במילים, בלי קוד.
הדירוג לפי **כיסוי ממדים** (רובריקה), לא לפי דמיון לתשובת AI כלשהי:
פתרון מקורי שמכסה את הממד מקבל ציון מלא, והציון מסביר את עצמו.

Flow:
  1. get_architecture_question(level)            → תרחיש + הממדים שייבדקו (שקוף)
  2. score_architecture_answer(question_id, ans) → Groq מציין כל ממד 0-100 + fallback

הממדים הקבועים (רובריקה):
  scalability · data_flow · failure_handling · security · tradeoffs
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
#  Rubric dimensions — fixed across all scenarios
# ──────────────────────────────────────────────

DIMENSIONS = [
    {"key": "scalability",      "he": "סקלביליות",    "weight": 0.25,
     "desc": "התמודדות עם גדילה ועומס — load balancing, cache, תורים, חלוקה"},
    {"key": "data_flow",        "he": "זרימת נתונים",  "weight": 0.20,
     "desc": "איך הנתונים זורמים בין הרכיבים — DB, API, pipeline"},
    {"key": "failure_handling", "he": "טיפול בכשלים",  "weight": 0.20,
     "desc": "מה קורה כשמשהו נשבר — retry, redundancy, ניטור, fallback"},
    {"key": "security",         "he": "אבטחה",         "weight": 0.20,
     "desc": "אימות, הרשאות, הצפנה, הגנה על מידע"},
    {"key": "tradeoffs",        "he": "Trade-offs",    "weight": 0.15,
     "desc": "הכרה בחלופות ובמחיר של ההחלטות — לא רק 'מה' אלא 'למה'"},
]

_DIM_KEYS = [d["key"] for d in DIMENSIONS]
_DIM_WEIGHT = {d["key"]: d["weight"] for d in DIMENSIONS}


# ──────────────────────────────────────────────
#  Scenario bank — system-design prompts, no code expected
# ──────────────────────────────────────────────

SCENARIOS: List[Dict] = [
    {
        "id": "ARCH_BUS_1",
        "level": 1,
        "title": "התראות אוטובוס בזמן אמת",
        "prompt": (
            "תכנן מערכת שמודיעה ל-100,000 משתמשים כשהאוטובוס שלהם במרחק 5 דקות.\n"
            "תאר במילים: אילו רכיבים יש, איך הם מדברים, ומה קורה בעומס. בלי קוד."
        ),
    },
    {
        "id": "ARCH_FRAUD_2",
        "level": 2,
        "title": "זיהוי הונאות בזמן אמת",
        "prompt": (
            "תכנן מערכת שמזהה עסקאות אשראי חשודות תוך פחות משנייה מרגע העסקה.\n"
            "תאר את הארכיטקטורה: איך מחליטים, מה קורה אם המערכת איטית, ואיך מגנים על המידע."
        ),
    },
    {
        "id": "ARCH_CHAT_3",
        "level": 3,
        "title": "צ'אט ל-10 מיליון משתמשים",
        "prompt": (
            "תכנן מערכת צ'אט שתומכת ב-10 מיליון משתמשים מחוברים בו-זמנית.\n"
            "תאר: איך הודעות מגיעות מיד, איך מתמודדים עם נפח, ומה קורה כששרת נופל."
        ),
    },
]

_BY_ID = {s["id"]: s for s in SCENARIOS}


# ──────────────────────────────────────────────
#  Public — get scenario (rubric shown, transparent)
# ──────────────────────────────────────────────

def get_architecture_question(level: int = 1) -> Dict:
    """מחזיר תרחיש תכנון + הממדים שייבדקו (שקיפות — זו רובריקה, לא תשובה)."""
    level = max(1, min(3, int(level)))
    s = next((x for x in SCENARIOS if x["level"] == level), SCENARIOS[0])
    return {
        "id":         s["id"],
        "level":      s["level"],
        "title":      s["title"],
        "prompt":     s["prompt"],
        "dimensions": [{"he": d["he"], "desc": d["desc"], "weight": d["weight"]} for d in DIMENSIONS],
    }


# ──────────────────────────────────────────────
#  Groq — rubric coverage (per dimension, not similarity)
# ──────────────────────────────────────────────

_ARCH_SYSTEM = (
    "You are evaluating a candidate's SYSTEM-DESIGN plan, written in plain language (no code expected). "
    "Score how well the plan COVERS each rubric dimension.\n\n"
    "Critical grading rules:\n"
    "• Reward correct, relevant coverage in ANY valid approach. Do NOT penalize a design just because "
    "it differs from a 'standard' or expected answer — originality that covers the dimension scores full.\n"
    "• A dimension the candidate did not address at all scores low (0-30). "
    "A dimension addressed thoughtfully scores high (70-100).\n"
    "• Do NOT reward verbosity, buzzwords, or fancy wording — reward genuine understanding only.\n\n"
    "Dimensions (score each 0-100):\n"
    "  scalability:      handling growth/load (load balancing, cache, queues, sharding)\n"
    "  data_flow:        how data moves between components (DB, API, pipeline)\n"
    "  failure_handling: what happens when something breaks (retry, redundancy, monitoring, fallback)\n"
    "  security:         auth, permissions, encryption, protecting data\n"
    "  tradeoffs:        acknowledging alternatives and the cost of decisions (the 'why', not just 'what')\n\n"
    'Return ONLY valid JSON: {"scalability": N, "data_flow": N, "failure_handling": N, '
    '"security": N, "tradeoffs": N, "feedback": "one short sentence in Hebrew naming the main gap"}'
)


def _call_groq_arch(scenario: Dict, answer: str) -> Optional[Dict]:
    if not GROQ_API_KEY or not answer.strip():
        return None
    try:
        import httpx
        user_msg = (
            f"Scenario: {scenario['title']}\n{scenario['prompt']}\n\n"
            f"Candidate's plan:\n{answer[:2000]}"
        )
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": _ARCH_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
            "max_tokens": 200,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        resp = httpx.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json=payload,
            timeout=10.0,
        )
        if resp.status_code != 200:
            return None
        parsed = json.loads(resp.json()["choices"][0]["message"]["content"])
        if not all(k in parsed for k in _DIM_KEYS):
            return None
        dims = {k: max(0.0, min(100.0, float(parsed[k]))) for k in _DIM_KEYS}
        total = round(sum(dims[k] * _DIM_WEIGHT[k] for k in _DIM_KEYS), 2)
        return {"dimensions": dims, "total": total, "feedback": parsed.get("feedback", "")}
    except Exception:
        return None


# Keyword cues per dimension — fallback only
_DIM_CUES = {
    "scalability":      ["scale", "load", "עומס", "cache", "מטמון", "queue", "תור", "shard", "horizontal",
                          "balanc", "איזון", "replica", "partition", "cdn", "מבוזר"],
    "data_flow":        ["database", "db", "מסד", "api", "pipeline", "צינור", "flow", "זרימה", "stream",
                          "message", "הודע", "event", "אירוע", "store", "אחסון"],
    "failure_handling": ["retry", "ניסיון", "fail", "כשל", "נפל", "redundan", "כפילות", "fallback",
                          "monitor", "ניטור", "alert", "התראה", "backup", "גיבוי", "recover", "health"],
    "security":         ["auth", "אימות", "הרשא", "permission", "encrypt", "הצפנ", "token", "טוקן",
                          "tls", "https", "secure", "אבטח", "מידע רגיש"],
    "tradeoffs":        ["tradeoff", "trade-off", "חלופ", "alternative", "but", "אבל", "instead", "במקום",
                          "cost", "מחיר", "עלות", "לעומת", "compromise", "פשרה", "why", "כי", "בגלל"],
}


def _heuristic_arch(scenario: Dict, answer: str) -> Dict:
    text = answer.lower()
    dims = {}
    for key, cues in _DIM_CUES.items():
        hits = sum(1 for c in cues if c in text)
        # 0 hits → ~20, 1 → ~50, 2 → ~70, 3+ → ~85
        dims[key] = float({0: 20, 1: 50, 2: 70}.get(hits, 85)) if hits < 3 else 85.0
    total = round(sum(dims[k] * _DIM_WEIGHT[k] for k in _DIM_KEYS), 2)
    weakest = min(dims, key=dims.get)
    he = next(d["he"] for d in DIMENSIONS if d["key"] == weakest)
    return {"dimensions": dims, "total": total, "feedback": f"ניתוח מבני — הממד החלש: {he}"}


def score_architecture_answer(question_id: str, answer: str) -> Dict:
    """
    מדרג תוכנית ארכיטקטורה לפי כיסוי 5 ממדים.
    מנסה Groq (רובריקה); fallback — היוריסטיקת cues per ממד.
    """
    s = _BY_ID.get(question_id)
    if not s:
        return {"score": 0.0, "error": f"תרחיש לא נמצא: {question_id}"}

    result = _call_groq_arch(s, answer)
    method = "groq"
    if not result:
        result = _heuristic_arch(s, answer)
        method = "heuristic"

    # Hebrew-labelled per-dimension breakdown for the UI
    breakdown = [
        {"key": k, "he": next(d["he"] for d in DIMENSIONS if d["key"] == k),
         "score": round(result["dimensions"][k], 1), "weight": _DIM_WEIGHT[k]}
        for k in _DIM_KEYS
    ]
    return {
        "score":     result["total"],
        "breakdown": breakdown,
        "feedback":  result.get("feedback", ""),
        "passes":    result["total"] >= 55,
        "method":    method,
    }


# ──────────────────────────────────────────────
#  CLI demo
# ──────────────────────────────────────────────

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    q = get_architecture_question(1)
    print(f"=== {q['title']} (level {q['level']}) ===")
    print(q["prompt"])
    print("\nממדי הערכה:")
    for d in q["dimensions"]:
        print(f"  • {d['he']} ({int(d['weight']*100)}%) — {d['desc']}")

    strong = (
        "אשתמש ב-message queue (Kafka) כדי לפזר עומס — כל עדכון מיקום אוטובוס נכנס לתור. "
        "שירות מתאמים בודק אילו משתמשים במרחק 5 דקות ושולח push notification דרך FCM. "
        "הנתונים זורמים: GPS → queue → matching service → notification service → משתמש. "
        "לסקיילינג אשתמש ב-cache (Redis) של מיקומי משתמשים ואחלק את העבודה לפי אזור גאוגרפי. "
        "אם שירות נופל — יש redundancy עם כמה instances ו-health checks שמפעילים מחדש. "
        "אבטחה: כל בקשה מאומתת ב-token, ומיקומי המשתמשים מוצפנים. "
        "Trade-off: בחרתי push על pull כי זה חוסך עומס, אבל המחיר הוא תלות בספק push חיצוני."
    )
    weak = "אני אבנה שרת שבודק כל הזמן איפה האוטובוס ושולח הודעה למשתמש."

    for label, ans in [("תוכנית חזקה", strong), ("תוכנית חלשה", weak)]:
        r = score_architecture_answer(q["id"], ans)
        print(f"\n— {label}: {r['score']}/100 ({r['method']}) passes={r['passes']}")
        for b in r["breakdown"]:
            print(f"    {b['he']:14s} {b['score']:.0f}")
        print(f"    feedback: {r['feedback']}")
