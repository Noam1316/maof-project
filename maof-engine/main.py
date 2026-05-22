"""
מעוף — Dual Scoring Engine
מנוע השיבוץ הראשי

הרצה:
  uvicorn main:app --reload
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from scoring.score_a import calculate_score_a
from scoring.score_b import calculate_score_b
from scoring.score_c import calculate_score_c
from scoring.volume import calculate_volume_score
from matching.hungarian import run_hungarian, calculate_total_value
from data.synthetic import generate_dataset
from models.candidate import Candidate
from models.school import School
from models.company import Company


def run_full_matching(
    candidates: list[Candidate],
    schools: list[School],
    companies: list[Company],
    total_placements: int = 0
) -> dict:
    """
    מריץ את כל תהליך השיבוץ:
    1. מחשב ציון A, B, C לכל שילוב
    2. מחשב ציון נפח
    3. מריץ Hungarian Algorithm
    4. מחזיר שיבוצים מסודרים
    """

    placement_ids = [f"{s.id}__{c.id}" for s in schools for c in companies]
    placements_list = [(s, c) for s in schools for c in companies]

    all_results = []
    final_matrix = []

    for candidate in candidates:
        row = []
        for school, company in placements_list:
            a = calculate_score_a(candidate, school)
            b = calculate_score_b(candidate, company)
            c = calculate_score_c(a, b, candidate, school, company, total_placements)
            vol = calculate_volume_score(a, b, c)

            row.append(vol["final_score"])
            all_results.append({
                "candidate_id": candidate.id,
                "school_id": school.id,
                "company_id": company.id,
                "score_a": a,
                "score_b": b,
                "score_c": c,
                "volume_score": vol["volume_score"],
                "final_score": vol["final_score"],
                "passes_threshold": vol["passes_threshold"],
            })

        final_matrix.append(row)

    # Hungarian
    candidate_ids = [c.id for c in candidates]
    assignments = run_hungarian(candidate_ids, placement_ids, final_matrix)
    total_value = calculate_total_value(assignments)

    return {
        "assignments": assignments,
        "total_value": total_value,
        "all_scores": all_results,
        "stats": {
            "candidates": len(candidates),
            "schools": len(schools),
            "companies": len(companies),
            "placements": len(placement_ids),
            "successful_assignments": len(assignments),
        }
    }


# --- הרצת דמו ---
if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("Maof — Dual Scoring Engine")
    print("=" * 50)

    # נתונים סינתטיים
    candidates, schools, companies = generate_dataset(
        n_candidates=5,
        n_schools=3,
        n_companies=3
    )

    print(f"מועמדים: {len(candidates)}")
    print(f"בתי ספר: {len(schools)}")
    print(f"חברות: {len(companies)}")
    print()

    # הרצת שיבוץ
    results = run_full_matching(candidates, schools, companies)

    print("שיבוצים אופטימליים:")
    print("-" * 40)
    for assignment in results["assignments"]:
        school_id, company_id = assignment["placement_id"].split("__")
        print(f"  {assignment['candidate_id']} → {school_id} + {company_id} | ציון: {assignment['final_score']}")

    print()
    print(f"ערך כולל: {results['total_value']}")
    print(f"שיבוצים מוצלחים: {results['stats']['successful_assignments']}/{results['stats']['candidates']}")
