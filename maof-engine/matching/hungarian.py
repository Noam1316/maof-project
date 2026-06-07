"""
Hungarian Algorithm — שיבוץ גלובלי אופטימלי
מעוף Tech-Lead Israel

run_hungarian:               שיבוץ קלאסי — מועמד אחד לכל (בי"ס, חברה)
run_hungarian_with_capacity: שיבוץ עם קיבולות — בי"ס יכול לקבל N מורים,
                             חברה יכולה לקבל M עובדים.

אלגוריתם קיבולות — iterative Hungarian:
  בכל סבב מריצים Hungarian על מועמדים שלא שובצו × זוגות (בי"ס,חברה)
  שעדיין יש להם קיבולת פנויה. לאחר כל סבב מורידים קיבולת ומסירים
  זוגות שמלאו. חוזרים עד שכולם שובצו או אין קיבולת.

ערובה:
  כל סבב מפיק שיבוץ Hungarian-optimal ביחס לנשארים.
  הפתרון הכולל הוא near-optimal (greedy round-robin),
  לא globally optimal — אך אופטימלי-למעשה לסדרי הגודל של המיזם.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment
from typing import List, Dict, Tuple


def build_cost_matrix(final_scores: List[List[float]]) -> np.ndarray:
    """
    בונה מטריצת עלות מציוני הנפח.
    Hungarian מינימיזציה — לכן נהפוך לעלות (100 - ציון).
    """
    matrix = np.array(final_scores, dtype=float)
    cost_matrix = np.where(matrix == 0, 200.0, 100.0 - matrix)
    return cost_matrix


def run_hungarian(
    candidates: List[str],
    placements: List[str],
    final_scores: List[List[float]]
) -> List[Dict]:
    """
    שיבוץ קלאסי — מועמד אחד לכל slot.

    candidates:   רשימת IDs של מועמדים
    placements:   רשימת IDs של שיבוצים (בית_ספר__חברה)
    final_scores: מטריצה [מועמד][שיבוץ] = ציון סופי
    """
    if not candidates or not placements:
        return []

    cost_matrix = build_cost_matrix(final_scores)
    row_ind, col_ind = linear_sum_assignment(cost_matrix)

    results = []
    for r, c in zip(row_ind, col_ind):
        score = final_scores[r][c]
        if score > 0:
            results.append({
                "candidate_id": candidates[r],
                "placement_id": placements[c],
                "final_score": score,
                "rank": None,
            })

    results.sort(key=lambda x: x["final_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1
    return results


def run_hungarian_with_capacity(
    candidates: List[str],
    schools: List,          # אובייקטים עם .id ו-.capacity
    companies: List,        # אובייקטים עם .id ו-.open_positions
    score_3d: List[List[List[float]]],  # [n_cand][n_school][n_company]
) -> List[Dict]:
    """
    שיבוץ עם קיבולות — iterative Hungarian.

    כל בי"ס מקבל עד school.capacity מועמדים.
    כל חברה מקבלת עד company.open_positions מועמדים.

    האלגוריתם:
      סבב 1: Hungarian על כל המועמדים × כל הזוגות הזמינים.
              לכל זוג (בי"ס,חברה) קיבולת = 1 בסבב.
              מעדכן קיבולות, מסיר מועמדים שהוצמדו.
      סבב 2: אותו דבר על המועמדים שנותרו.
      חוזרים עד max(max_school_cap, max_company_cap) סבבים.

    מחזיר:
      רשימת dict עם candidate_id, school_id, company_id, final_score, rank.
    """
    n_c = len(candidates)
    n_s = len(schools)
    n_k = len(companies)

    school_cap = {s.id: getattr(s, 'capacity', 1) for s in schools}
    company_cap = {c.id: getattr(c, 'open_positions', 1) for c in companies}

    placed: Dict[str, dict] = {}
    unplaced = list(range(n_c))

    max_rounds = max(max(school_cap.values()), max(company_cap.values()), 1)

    for _ in range(max_rounds + 1):
        if not unplaced:
            break

        # זוגות (בי"ס, חברה) עם קיבולת פנויה
        available = [
            (si, ci, schools[si].id, companies[ci].id)
            for si in range(n_s)
            for ci in range(n_k)
            if school_cap[schools[si].id] > 0 and company_cap[companies[ci].id] > 0
        ]
        if not available:
            break

        # מטריצת ציונים: [מועמדים שלא שובצו] × [זוגות זמינים]
        sub = [
            [score_3d[c_idx][si][ci] for si, ci, _, _ in available]
            for c_idx in unplaced
        ]
        cost = build_cost_matrix(sub)
        row_ind, col_ind = linear_sum_assignment(cost)

        # מיון לפי ציון יורד — הטוב ביותר נשבץ ראשון במקרה של תחרות על קיבולת
        assignments = [
            (score_3d[unplaced[r]][available[c][0]][available[c][1]], r, c)
            for r, c in zip(row_ind, col_ind)
        ]
        assignments.sort(reverse=True)

        newly_placed = []
        for score, r, c in assignments:
            c_idx = unplaced[r]
            si, ci, s_id, co_id = available[c]
            if score <= 0:
                continue
            # בדיקת קיבולת — עשויה להיות מוקטנת מהקצאות קודמות בסבב זה
            if school_cap[s_id] > 0 and company_cap[co_id] > 0:
                placed[candidates[c_idx]] = {
                    "candidate_id": candidates[c_idx],
                    "school_id":    s_id,
                    "company_id":   co_id,
                    "final_score":  round(score, 2),
                    "rank":         None,
                }
                school_cap[s_id]  -= 1
                company_cap[co_id] -= 1
                newly_placed.append(c_idx)

        unplaced = [c for c in unplaced if c not in newly_placed]
        if not newly_placed:
            break  # אין התקדמות — עצור

    results = sorted(placed.values(), key=lambda x: x["final_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1
    return results


def calculate_total_value(results: List[Dict]) -> float:
    return round(sum(r["final_score"] for r in results), 2)
