"""
Semantic Match — התאמה סמנטית בין מיומנויות
מעוף Tech-Lead Israel

מחליף keyword matching פשוט בהשוואה סמנטית אמיתית.
Fallback: Jaccard + מילון נרדפות ידני (ללא מודל).
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import List, Optional
import re

# --- מילון נרדפות טכנולוגי ---
SYNONYMS = {
    "סייבר": ["cyber", "אבטחת מידע", "information security", "cybersecurity", "network security", "אבטחה"],
    "פייתון": ["python", "py", "python3"],
    "מתמטיקה": ["math", "mathematics", "אלגברה", "חשבון", "סטטיסטיקה", "statistics"],
    "מדעי מחשב": ["computer science", "cs", "תכנות", "programming", "coding"],
    "פיזיקה": ["physics", "מכניקה", "תרמודינמיקה"],
    "נתונים": ["data science", "data", "big data", "analytics", "ניתוח נתונים", "ml", "machine learning"],
    "רשתות": ["networking", "networks", "network", "tcp/ip", "cisco"],
    "ענן": ["cloud", "aws", "azure", "gcp", "devops"],
    "אלגוריתמים": ["algorithms", "data structures", "מבני נתונים"],
    "ai": ["artificial intelligence", "בינה מלאכותית", "machine learning", "deep learning", "llm"],
    "web": ["javascript", "react", "node", "frontend", "backend", "fullstack", "html", "css"],
    "java": ["jvm", "spring", "kotlin"],
    "c": ["c++", "c#", "embedded", "firmware"],
}


def _normalize(text: str) -> str:
    return text.lower().strip()


def _expand_with_synonyms(terms: List[str]) -> set:
    """מרחיב רשימת מונחים עם נרדפות"""
    expanded = set()
    for term in terms:
        t = _normalize(term)
        expanded.add(t)
        # חפש בכל קבוצת נרדפות
        for canonical, synonyms in SYNONYMS.items():
            all_forms = [_normalize(canonical)] + [_normalize(s) for s in synonyms]
            if t in all_forms:
                expanded.update(all_forms)
    return expanded


def semantic_similarity_simple(terms_a: List[str], terms_b: List[str]) -> float:
    """
    Jaccard similarity עם הרחבת נרדפות.
    עובד ללא מודל — מהיר ואמין לטכנולוגיות.
    """
    if not terms_a or not terms_b:
        return 0.0

    set_a = _expand_with_synonyms(terms_a)
    set_b = _expand_with_synonyms(terms_b)

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    return round(intersection / union, 3) if union > 0 else 0.0


def semantic_similarity_transformers(terms_a: List[str], terms_b: List[str]) -> Optional[float]:
    """
    Cosine similarity עם sentence-transformers.
    מדויק יותר — מבין משמעות עמוקה.
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        text_a = " ".join(terms_a)
        text_b = " ".join(terms_b)
        embeddings = model.encode([text_a, text_b])
        dot = np.dot(embeddings[0], embeddings[1])
        norm = np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        return round(float(dot / norm), 3) if norm > 0 else 0.0
    except Exception:
        return None


def get_semantic_similarity(terms_a: List[str], terms_b: List[str]) -> dict:
    """
    מחשב similarity סמנטי — מנסה transformers, fallback ל-Jaccard+נרדפות.
    מחזיר: score (0-1), method, normalized (0-100).
    """
    transformer_score = semantic_similarity_transformers(terms_a, terms_b)

    if transformer_score is not None:
        return {
            "score": transformer_score,
            "method": "sentence-transformers",
            "normalized": round(min(100.0, transformer_score * 120), 1),  # cosine בד"כ 0-0.85
        }

    jaccard = semantic_similarity_simple(terms_a, terms_b)
    return {
        "score": jaccard,
        "method": "jaccard+synonyms",
        "normalized": round(min(100.0, jaccard * 150), 1),  # Jaccard scale → 100
    }


def subject_semantic_score(candidate_subjects: List[str], required_subjects: List[str]) -> float:
    """
    ציון התאמת מקצוע סמנטי (0-100).
    משמש ב-score_a.subject_match_score.
    """
    if not required_subjects:
        return 80.0

    scores = []
    for req in required_subjects:
        # בדוק התאמה מדויקת קודם
        req_norm = _normalize(req)
        exact = any(_normalize(c) == req_norm for c in candidate_subjects)
        if exact:
            scores.append(100.0)
            continue

        # similarity סמנטי
        sim = get_semantic_similarity(candidate_subjects, [req])
        scores.append(sim["normalized"])

    return round(sum(scores) / len(scores), 2) if scores else 0.0


def tech_stack_semantic_score(candidate_stack: List[str], company_stack: List[str]) -> float:
    """
    ציון התאמת Tech Stack סמנטי (0-100).
    משמש ב-score_b.tech_skills_score.
    """
    if not company_stack:
        return 80.0
    if not candidate_stack:
        return 20.0

    # Jaccard+נרדפות עם נירמול
    sim = get_semantic_similarity(candidate_stack, company_stack)

    # Jaccard של 0.5+ = 100 נקודות (overlap חצי = מצוין)
    score = min(100.0, sim["score"] * 200)
    return round(score, 2)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print("Semantic Match — Demo")
    print("=" * 50)

    tests = [
        (["סייבר", "פייתון"], ["cyber", "python"], "עברית vs אנגלית"),
        (["אבטחת מידע", "רשתות"], ["סייבר", "networking"], "נרדפות"),
        (["Python", "AI", "Data Science"], ["Machine Learning", "Python", "Analytics"], "Tech Stack"),
        (["Java", "Spring"], ["Python", "Django"], "אין חפיפה"),
    ]

    for a, b, label in tests:
        sim = get_semantic_similarity(a, b)
        print(f"\n{label}:")
        print(f"  A: {a}")
        print(f"  B: {b}")
        print(f"  Score: {sim['score']} | Normalized: {sim['normalized']}/100 | Method: {sim['method']}")
