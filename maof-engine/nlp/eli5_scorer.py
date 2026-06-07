"""
ELI5 Scorer — נקודת כניסה מרכזית למנוע ELI5
מעוף Tech-Lead Israel

מחשב ציון ELI5 מטקסט גולמי:
  ELI5_keyword × 0.65 + ELI5_Groq × 0.35

אם אין Groq key או Groq נכשל — fallback ל-keyword בלבד.
אם אין טקסט — מחזיר את הציון הגולמי שהוזן ישירות.
"""

from typing import Optional
from nlp.groq_eli5 import analyze_eli5_full


def compute_eli5_score(text: Optional[str], topic: str = "", fallback_score: float = 0.0) -> float:
    """
    מחשב ציון ELI5 מטקסט.

    text:           טקסט ההסבר של המועמד
    topic:          נושא ההסבר (לציון דיוק) — אופציונלי
    fallback_score: ציון גולמי לשימוש כשאין טקסט (e.g. מ-synthetic data)

    מחזיר ציון 0–100.
    """
    if not text or len(text.strip()) < 10:
        return round(float(fallback_score), 2)

    result = analyze_eli5_full(text, topic)
    return result["total_score"]


def compute_eli5_detailed(text: Optional[str], topic: str = "", fallback_score: float = 0.0) -> dict:
    """
    מחזיר ניתוח מלא של ELI5 — לשימוש ב-API ובדוחות.

    תמיד מחזיר dict תקין עם total_score, breakdown, feedback.
    """
    if not text or len(text.strip()) < 10:
        return {
            "total_score": round(float(fallback_score), 2),
            "passes_minimum": fallback_score >= 60,
            "breakdown": {},
            "feedback": ["לא הוזן טקסט — ציון גולמי"],
            "groq": None,
            "llm_enhanced": False,
            "scoring_method": "fallback",
        }

    return analyze_eli5_full(text, topic)
