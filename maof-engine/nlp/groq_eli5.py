"""
Groq ELI5 Quality Layer — מעוף Tech-Lead Israel
================================================
Adds LLM-based quality scoring on top of the keyword analyzer.
Uses Groq (llama-3.3-70b-versatile) — free tier, 6000 req/day.

Scores 3 things keywords CANNOT catch:
  1. analogy_quality   — is the analogy actually relevant? (not just present)
  2. conclusion_logic  — does the conclusion follow from the body?
  3. audience_fit      — is the language right for a non-expert?

Usage:
  from nlp.groq_eli5 import score_with_groq, analyze_eli5_full

  # Full analysis (keyword + Groq)
  result = analyze_eli5_full(text, topic="סייבר")

  # Groq only (if you have the keyword result already)
  groq_result = score_with_groq(text)

Requires: GROQ_API_KEY in environment or .env file
Fallback:  if no key or timeout → returns None, caller uses keyword score only
"""

import os
import sys
# Make sure 'maof-engine/' is on the path so 'from nlp.X import Y' works
# regardless of which directory the script is run from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import re
import time
from typing import Optional, Dict

from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"
GROQ_URL     = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_S    = 8.0

# Weight blend: keyword vs Groq
KEYWORD_WEIGHT = 0.55
GROQ_WEIGHT    = 0.45

# Prompt — short, structured, JSON output
SYSTEM_PROMPT = (
    "You are an expert evaluator of ELI5 explanations (Explain Like I'm 5). "
    "Evaluate the given text and return ONLY valid JSON with exactly these keys:\n"
    '{"analogy_quality": 0-100, "conclusion_logic": 0-100, "audience_fit": 0-100, "reasoning": "one short sentence"}\n\n'
    "Scoring guide:\n"
    "  analogy_quality:  Is the analogy actually relevant and illuminating? "
    "High if it genuinely clarifies; low if forced, missing, or off-topic.\n"
    "  conclusion_logic: Does the final takeaway logically follow from the explanation? "
    "High if it feels like a real insight; low if it's just stuck on.\n"
    "  audience_fit:     Is the vocabulary and framing right for a non-expert? "
    "High if a 12-year-old could follow; low if jargon or assumed knowledge.\n"
    "Return ONLY the JSON object, no extra text."
)


def _call_groq(text: str) -> Optional[Dict]:
    """Raw Groq API call. Returns parsed JSON or None on any failure."""
    if not GROQ_API_KEY:
        return None

    try:
        import httpx

        user_msg = f"Evaluate this ELI5 explanation:\n\n{text[:1200]}"

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            "max_tokens": 120,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        t0 = time.time()
        resp = httpx.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type":  "application/json",
            },
            json=payload,
            timeout=TIMEOUT_S,
        )
        latency_ms = round((time.time() - t0) * 1000)

        if resp.status_code != 200:
            return None

        content = resp.json()["choices"][0]["message"]["content"]
        parsed  = json.loads(content)

        # validate expected keys exist and are numeric
        required = {"analogy_quality", "conclusion_logic", "audience_fit"}
        if not required.issubset(parsed.keys()):
            return None
        for k in required:
            parsed[k] = max(0.0, min(100.0, float(parsed[k])))

        parsed["latency_ms"] = latency_ms
        return parsed

    except Exception:
        return None


def score_with_groq(text: str) -> Optional[Dict]:
    """
    Returns Groq quality scores + composite, or None if unavailable.

    {
      "analogy_quality": float,
      "conclusion_logic": float,
      "audience_fit": float,
      "groq_composite": float,   # weighted average of the 3
      "reasoning": str,
      "latency_ms": int,
    }
    """
    result = _call_groq(text)
    if result is None:
        return None

    composite = round(
        result["analogy_quality"]  * 0.40 +
        result["conclusion_logic"] * 0.35 +
        result["audience_fit"]     * 0.25,
        2,
    )
    result["groq_composite"] = composite
    return result


def blend_scores(keyword_score: float, groq_composite: float) -> float:
    """Blend keyword + Groq into a single final score."""
    return round(
        keyword_score  * KEYWORD_WEIGHT +
        groq_composite * GROQ_WEIGHT,
        2,
    )


def analyze_eli5_full(text: str, topic: str = "") -> Dict:
    """
    Full ELI5 analysis: keyword layer + optional Groq layer.

    Always returns a complete result dict.
    If Groq is unavailable, falls back gracefully to keyword-only.

    Extra keys vs analyze_eli5():
      "groq": dict or None
      "llm_enhanced": bool
      "scoring_method": "keyword+groq" | "keyword-only"
    """
    from nlp.eli5_analyzer import analyze_eli5

    base = analyze_eli5(text)
    groq = score_with_groq(text)

    if groq is not None:
        final_score = blend_scores(base["total_score"], groq["groq_composite"])

        # rebuild feedback: drop keyword items that Groq overrides
        feedback = list(base["feedback"])
        if groq["analogy_quality"] >= 70 and "אנלוגיות" in " ".join(feedback):
            feedback = [f for f in feedback if "אנלוגיות" not in f]
        if groq["audience_fit"] < 60:
            feedback.append("הסבר טכני מדי — נסה להסביר כאילו לחבר שלא מהתחום")
        if groq["conclusion_logic"] < 60:
            feedback.append("המסקנה לא נובעת ישירות מההסבר — חזק את הקשר הלוגי")

        return {
            "total_score":    final_score,
            "passes_minimum": final_score >= 60,
            "breakdown":      base["breakdown"],
            "feedback":       feedback if feedback else ["הסבר טוב! המשך כך"],
            "groq": {
                "analogy_quality":  groq["analogy_quality"],
                "conclusion_logic": groq["conclusion_logic"],
                "audience_fit":     groq["audience_fit"],
                "groq_composite":   groq["groq_composite"],
                "reasoning":        groq.get("reasoning", ""),
                "latency_ms":       groq.get("latency_ms", 0),
            },
            "llm_enhanced":    True,
            "scoring_method":  "keyword+groq",
        }

    # Groq unavailable — return keyword result with extra metadata
    base["groq"]           = None
    base["llm_enhanced"]   = False
    base["scoring_method"] = "keyword-only"
    return base


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    # Windows PowerShell RTL fix
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

    test_cases = [
        {
            "label": "GOOD — hook + analogy + conclusion",
            "text": (
                "דמיין שאתה מנסה להסביר לילד איך עובד האינטרנט. "
                "זה כמו ספרייה ענקית שאפשר להגיע אליה מכל מקום. "
                "כל אתר הוא ספר, וה-URL זה הכתובת שלו על המדף. "
                "לכן, ככל שהכתובת מדויקת יותר — מוצאים את הספר מהר יותר."
            ),
        },
        {
            "label": "BAD — jargon, no analogy, no conclusion",
            "text": (
                "האינטרנט הוא רשת תקשורת גלובלית המבוססת על פרוטוקול TCP/IP. "
                "הנתונים מועברים בחבילות דרך נתבים ושרתים. "
                "כל מכשיר מקבל כתובת IP ייחודית לזיהוי ברשת."
            ),
        },
    ]

    key_avail = bool(GROQ_API_KEY)
    print(f"GROQ_API_KEY: {'set' if key_avail else 'NOT SET — keyword-only mode'}")
    print()

    for tc in test_cases:
        print(f"{'=' * 58}")
        print(f"  {tc['label']}")
        print(f"{'=' * 58}")
        r = analyze_eli5_full(tc["text"])
        print(f"  Score  : {r['total_score']}  |  method: {r['scoring_method']}")
        print(f"  Passes : {r['passes_minimum']}")
        if r["groq"]:
            g = r["groq"]
            print(f"  Groq   : analogy={g['analogy_quality']}  logic={g['conclusion_logic']}  audience={g['audience_fit']}")
            print(f"           composite={g['groq_composite']}  latency={g['latency_ms']}ms")
            print(f"           reasoning: {g['reasoning']}")
        print(f"  Feedback: {r['feedback']}")
        print()
