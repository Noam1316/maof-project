"""
Weight Store — persistent JSON storage for learned weights
מעוף Tech-Lead Israel

שומר ומשחזר משקלות שנלמדו מ:
  1. Genetic Algorithm (משקלות רכיבים)
  2. Feedback Loop (משקלות volume/A/B בנוסחה הסופית)

כל עדכון נשמר ל-weights.json בתיקיית feedback/.
ברירת מחדל = המשקלות המקוריות מהמפרט.
"""

import json
import os
from typing import Dict

WEIGHTS_FILE = os.path.join(os.path.dirname(__file__), "weights.json")

DEFAULT_WEIGHTS: Dict = {
    "score_a": {
        "eli5": 0.35,
        "subject": 0.25,
        "retention": 0.25,
        "impact": 0.15,
    },
    "score_b": {
        "tech": 0.35,
        "growth": 0.25,
        "soft": 0.25,
        "culture": 0.15,
    },
    "volume": {
        "volume_score": 0.50,
        "score_a": 0.25,
        "score_b": 0.25,
    },
    "source": "default",
    "updated_at": None,
    "n_records_used": 0,
}


def load_weights() -> Dict:
    """טוען משקלות מקובץ. מחזיר ברירות מחדל אם הקובץ לא קיים או פגום."""
    if os.path.exists(WEIGHTS_FILE):
        try:
            with open(WEIGHTS_FILE, "r", encoding="utf-8") as f:
                stored = json.load(f)
            # מיזוג עם ברירות מחדל — מגן מפני שדות חסרים בגרסאות ישנות
            merged = {**DEFAULT_WEIGHTS, **stored}
            merged["score_a"] = {**DEFAULT_WEIGHTS["score_a"], **stored.get("score_a", {})}
            merged["score_b"] = {**DEFAULT_WEIGHTS["score_b"], **stored.get("score_b", {})}
            merged["volume"]  = {**DEFAULT_WEIGHTS["volume"],  **stored.get("volume",  {})}
            return merged
        except Exception:
            pass
    return dict(DEFAULT_WEIGHTS)


def save_weights(weights: Dict, source: str = "manual") -> None:
    """שומר משקלות לקובץ עם timestamp ומקור."""
    from datetime import datetime
    to_save = {**weights, "source": source, "updated_at": datetime.now().isoformat()}
    os.makedirs(os.path.dirname(WEIGHTS_FILE), exist_ok=True)
    with open(WEIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(to_save, f, indent=2, ensure_ascii=False)


def reset_to_defaults() -> Dict:
    """מאפס לברירות מחדל."""
    save_weights(DEFAULT_WEIGHTS, source="reset")
    return load_weights()


def get_weight_info() -> Dict:
    """מחזיר מידע על המשקלות הנוכחיות ומקורן."""
    w = load_weights()
    return {
        "source": w.get("source", "default"),
        "updated_at": w.get("updated_at"),
        "n_records_used": w.get("n_records_used", 0),
        "score_a": w["score_a"],
        "score_b": w["score_b"],
        "volume": w["volume"],
    }
