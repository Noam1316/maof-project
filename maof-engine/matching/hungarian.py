"""
Hungarian Algorithm — שיבוץ גלובלי אופטימלי
מעוף Tech-Lead Israel

מוצא את השיבוץ שמקסם את הסכום הכולל של ציוני הנפח
לכל השוק בו-זמנית — לא מקסום לזוג אחד.
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
    מריץ Hungarian Algorithm ומחזיר רשימת שיבוצים אופטימלית.

    candidates: רשימת IDs של מועמדים
    placements: רשימת IDs של בית_ספר__חברה
    final_scores: מטריצה [מועמד][שיבוץ] = ציון סופי

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
