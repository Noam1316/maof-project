"""
ציון נפח — הלב של האלגוריתם
מעוף Tech-Lead Israel

נפח = (A - 60) × (B - 60) × (C - 60)
ציון נפח = ∛נפח ÷ 40 × 100

ציון סופי = ציון נפח × 0.5 + A × 0.25 + B × 0.25

סף מינימום: 60 בכל ציון
"""

MIN_THRESHOLD = 60.0


def calculate_volume_score(score_a: float, score_b: float, score_c: float) -> dict:
    """
    מחשב ציון נפח וציון סופי.

    מחזיר dict עם:
      - passes_threshold: האם עבר סף מינימום
      - volume_score: ציון הנפח (0-100)
      - final_score: ציון סופי לשיבוץ (0-100)
      - breakdown: פירוט הציונים
    """

    # בדיקת סף מינימום
    if score_a < MIN_THRESHOLD or score_b < MIN_THRESHOLD or score_c < MIN_THRESHOLD:
        return {
            "passes_threshold": False,
            "volume_score": 0.0,
            "final_score": 0.0,
            "breakdown": {
                "score_a": score_a,
                "score_b": score_b,
                "score_c": score_c,
                "reason": f"לא עבר סף מינימום {MIN_THRESHOLD}"
            }
        }

    # חישוב נפח
    volume = (score_a - 60) * (score_b - 60) * (score_c - 60)

    if volume == 0:
        # Fallback: מועמד מצוין בשניים אבל צד שלישי בדיוק בסף —
        # עונש של volume=0 קשה מדי. משתמשים בממוצע גיאומטרי של
        # שני הציונים הגבוהים, עם תקרה 50 (פחות מ-balance מלא).
        margins = sorted(
            [score_a - 60, score_b - 60, score_c - 60], reverse=True
        )
        two_dim = (margins[0] * margins[1]) ** 0.5
        volume_score = round(min(50.0, two_dim / 40 * 100), 2)
    else:
        # ציון נפח — שורש שלישי מנורמל
        volume_score = (volume ** (1/3)) / 40 * 100
        volume_score = round(min(100.0, max(0.0, volume_score)), 2)

    # ציון סופי
    final_score = (
        volume_score * 0.50 +
        score_a * 0.25 +
        score_b * 0.25
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
            "volume": round(volume, 2),
        }
    }


# --- דוגמאות מהמפרט ---
if __name__ == "__main__":
    examples = [
        (95, 95, 95),
        (95, 95, 60),
        (75, 75, 75),
        (59, 95, 95),
    ]

    for a, b, c in examples:
        result = calculate_volume_score(a, b, c)
        print(f"A={a} B={b} C={c} → נפח={result['volume_score']} סופי={result['final_score']} {'✅' if result['passes_threshold'] else '❌'}")
