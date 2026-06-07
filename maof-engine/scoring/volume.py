"""
ציון נפח — הלב של האלגוריתם
מעוף Tech-Lead Israel

נוסחה מקורית (hard threshold):
  volume = (A-60)(B-60)(C-60)  → אפס אם אחד מהם < 60

נוסחה חדשה (soft threshold):
  gate  = σ(A) × σ(B) × σ(C)     σ = sigmoid סביב 60, steepness=0.25
  volume = gate × (A-50)(B-50)(C-50)

השינוי:
  לפני: A=59.9 → score=0, A=60.1 → score=74 (cliff של 74 נקודות על 0.2 הפרש)
  אחרי: A=59.9 → score≈62, A=60.1 → score≈63 (מעבר חלק)

ה-gate מדכא ציונים ב-55-65 (gate<0.73) ומשחרר ציונים ≥70 (gate>0.92).
MIN_THRESHOLD=55 נשאר כ-hard floor לדחייה מוחלטת (ציון <55 בממד כלשהו).

ציון סופי = vol_score × 0.5 + A × 0.25 + B × 0.25
"""

import math
from feedback.weight_store import load_weights as _load_weights

MIN_THRESHOLD  = 55.0   # hard floor — מתחת לזה: דחייה מוחלטת (היה 60)
SOFT_THRESHOLD = 60.0   # מרכז ה-sigmoid
SOFT_STEEPNESS = 0.25   # חדות המעבר (0.25 → מעבר חלק על ~20 נקודות)
VOLUME_BASE    = 50.0   # בסיס לחישוב נפח (היה 60, הורד כדי לתמוך ב-55-60)

_WV = _load_weights()["volume"]


def soft_gate(x: float) -> float:
    """
    Sigmoid gate סביב SOFT_THRESHOLD.
    x=55 → 0.22,  x=60 → 0.50,  x=65 → 0.78,  x=70 → 0.92,  x=80 → 0.99
    """
    return 1.0 / (1.0 + math.exp(-SOFT_STEEPNESS * (x - SOFT_THRESHOLD)))


def calculate_volume_score(score_a: float, score_b: float, score_c: float) -> dict:
    """
    מחשב ציון נפח וציון סופי עם soft threshold.

    passes_threshold=False רק אם אחד הציונים < MIN_THRESHOLD (55).
    """

    # Hard floor — מתחת ל-55 בממד כלשהו: דחייה מוחלטת
    if score_a < MIN_THRESHOLD or score_b < MIN_THRESHOLD or score_c < MIN_THRESHOLD:
        return {
            "passes_threshold": False,
            "volume_score": 0.0,
            "final_score": 0.0,
            "breakdown": {
                "score_a": score_a,
                "score_b": score_b,
                "score_c": score_c,
                "gate": 0.0,
                "reason": f"ציון מתחת ל-{MIN_THRESHOLD} בממד כלשהו",
            }
        }

    # Soft gate — מדכא ציונים קרובים ל-60, מפחית cliff
    gate = soft_gate(score_a) * soft_gate(score_b) * soft_gate(score_c)

    # נפח — בסיס 50 (נמוך מ-60 הישן, מאפשר ציוני 55-60 לתרום)
    raw_volume = (score_a - VOLUME_BASE) * (score_b - VOLUME_BASE) * (score_c - VOLUME_BASE)
    volume = gate * max(0.0, raw_volume)

    # ציון נפח — שורש שלישי מנורמל (אותה נורמליזציה כמו קודם)
    volume_score = (volume ** (1 / 3)) / 40 * 100
    volume_score = round(min(100.0, max(0.0, volume_score)), 2)

    # ציון סופי
    final_score = (
        volume_score * _WV["volume_score"] +
        score_a      * _WV["score_a"] +
        score_b      * _WV["score_b"]
    )
    final_score = round(min(100.0, max(0.0, final_score)), 2)

    return {
        "passes_threshold": True,
        "volume_score": volume_score,
        "final_score": final_score,
        "breakdown": {
            "score_a": score_a,
            "score_b": score_b,
            "score_c": score_c,
            "gate": round(gate, 4),
            "volume": round(volume, 2),
        }
    }


# --- דוגמאות מהמפרט ---
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    print("Soft Threshold Demo — before vs after")
    print("=" * 60)
    print(f"{'Case':<30} {'Old (hard)':<14} {'New (soft)'}")
    print("-" * 60)

    cases = [
        ("A=59.9 B=90 C=90 (cliff case)", 59.9, 90, 90),
        ("A=60.1 B=90 C=90",              60.1, 90, 90),
        ("A=55   B=90 C=90",              55.0, 90, 90),
        ("A=65   B=65 C=65",              65.0, 65, 65),
        ("A=75   B=75 C=75",              75.0, 75, 75),
        ("A=80   B=80 C=80",              80.0, 80, 80),
        ("A=95   B=95 C=95",              95.0, 95, 95),
        ("A=54   B=90 C=90 (hard floor)", 54.0, 90, 90),
    ]

    def old_score(a, b, c):
        if a < 60 or b < 60 or c < 60:
            return 0.0
        vol = (a-60)*(b-60)*(c-60)
        vs = min(100, (vol**(1/3))/40*100)
        return round(vs*0.5 + a*0.25 + b*0.25, 2)

    for label, a, b, c in cases:
        new = calculate_volume_score(a, b, c)
        old = old_score(a, b, c)
        gate = round(soft_gate(a) * soft_gate(b) * soft_gate(c), 3)
        print(f"  {label:<28} {old:<14} {new['final_score']}  (gate={gate})")
