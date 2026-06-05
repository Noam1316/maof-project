"""
Hungarian Algorithm — שיבוץ גלובלי אופטימלי
מעוף Tech-Lead Israel

מוצא את ההשמה שממזערת את סכום העלויות הכולל
(שקול למקסום סכום הציונים) — לא מקסום לזוג בודד.

הערה על הממד:
  הבעיה היא תלת-צדדית (מועמד × בית_ספר × חברה = F_ijk).
  הפתרון: מייצרים את כל צמדי (בית_ספר, חברה) כ"שיבוץ" בודד,
  ואז מריצים Hungarian דו-ממדי על מועמדים × שיבוצים.
  זו רדוקציה לגיטימית של בעיית 3 צדדים לבעיית השמה קלאסית.

ערובה:
  Hungarian מוצא פתרון אופטימלי גלובלית ביחס לפונקציית
  העלות שהוגדרה — לא "stable matching" במובן Gale-Shapley.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Dict, Tuple


def build_cost_matrix(final_scores: List[List[float]]) -> np.ndarray:
    """
    בונה מטריצת עלות מציוני הנפח.
    Hungarian מינימיזציה — לכן נהפוך לעלות (100 - ציון).
    """
    matrix = np.array(final_scores)
    # מועמד שלא עובר סף = עלות גבוהה מאוד
    matrix = np.where(matrix == 0, -1, matrix)
    cost_matrix = 100 - matrix
    return cost_matrix


def run_hungarian(
    candidates: List[str],
    placements: List[str],
    final_scores: List[List[float]]
) -> List[Dict]:
    """
    מריץ Hungarian Algorithm ומחזיר השמה אופטימלית גלובלית.

    candidates:   רשימת IDs של מועמדים
    placements:   רשימת IDs של שיבוצים (בית_ספר__חברה)
    final_scores: מטריצה [מועמד][שיבוץ] = ציון סופי

    הערובה: פתרון אופטימלי ביחס לסכום העלויות הכולל.
    כלומר, אין החלפת שני שיבוצים שתשפר את הסכום הכולל —
    אך זה שונה מ-"stable matching" (Gale-Shapley) שמתייחס
    להעדפות הדדיות של הצדדים.

    מחזיר: רשימת dict עם candidate_id, placement_id, score
    """
    if not candidates or not placements:
        return []

    cost_matrix = build_cost_matrix(final_scores)

    # Hungarian
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    results = []
    for r, c in zip(row_ind, col_ind):
        score = final_scores[r][c]
        if score > 0:  # עבר סף מינימום
            results.append({
                "candidate_id": candidates[r],
                "placement_id": placements[c],
                "final_score": score,
                "rank": None  # יחושב בהמשך
            })

    # מיון לפי ציון
    results.sort(key=lambda x: x["final_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return results


def calculate_total_value(results: List[Dict]) -> float:
    """סכום כולל של ציוני השיבוץ — מדד איכות השיבוץ הגלובלי"""
    return round(sum(r["final_score"] for r in results), 2)
