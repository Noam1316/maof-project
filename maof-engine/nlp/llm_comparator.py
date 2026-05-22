"""
LLM Comparator — השוואת הסבר מועמד להסבר LLM
מעוף Tech-Lead Israel

שלב 1: LLM (Claude/OpenAI) מייצר הסבר אידיאלי לנושא
שלב 2: sentence-transformers מודד similarity סמנטי
שלב 3: אם המועמד דומה מספיק (similarity > 0.75) AND קצר יותר → בונוס

Fallback: אם אין API Key → sentence-transformers בלבד עם reference מוכן מראש.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import math
from typing import Optional, Dict
from dotenv import load_dotenv

load_dotenv()

# --- Reference explanations (fallback — ללא API) ---
REFERENCE_EXPLANATIONS = {
    "סייבר": """
    סייבר זה כמו מנעול על הדלת של המחשב שלך.
    דמיין שהמחשב שלך הוא בית. אנשים רעים רוצים להיכנס ולגנוב דברים.
    אנשי סייבר הם השומרים שמוודאים שהמנעול חזק ושאף אחד לא יכול לפרוץ.
    לדוגמה, כשאתה מכניס סיסמה, זה כמו מפתח. אם הסיסמה חלשה, גנב יכול לנחש.
    לכן חשוב להיות חכמים ולהשתמש במפתחות חזקים.
    """,
    "פייתון": """
    פייתון זה שפה שבה מדברים עם המחשב, כמו שאנחנו מדברים בעברית.
    דמיין שאתה רוצה להכין עוגה. אתה צריך מתכון עם הוראות ברורות.
    פייתון זה המתכון שהמחשב מבין. כל שורה היא הוראה אחת.
    לדוגמה, אם תכתוב 'הדפס שלום', המחשב ידפיס שלום — פשוט ככה.
    לכן פייתון נחשב לשפה הכי קלה ללמידה.
    """,
    "מתמטיקה": """
    מתמטיקה זה כמו שפה שכל המחשבים והמדענים בעולם מבינים.
    דמיין שיש לך 5 תפוחים ונתת 2 לחבר. נשארו לך 3. זה מתמטיקה.
    אבל מתמטיקה עושה גם דברים מורכבים יותר, כמו לחשב איך טיל יטוס לירח.
    לדוגמה, כשבנק מחשב ריבית על חשבון, הוא משתמש במתמטיקה.
    לכן מתמטיקה היא הבסיס לכל המדע והטכנולוגיה.
    """,
    "default": """
    נושא זה כמו פאזל — יש הרבה חלקים קטנים שמתחברים לתמונה גדולה.
    דמיין שאתה לומד משהו חדש. בהתחלה זה נשמע מסובך.
    אבל אם מחלקים לחלקים קטנים ומבינים כל חלק — זה נהיה פשוט.
    לדוגמה, כמו שלמדת לקרוא — קודם אותיות, אחר כך מילים, אחר כך משפטים.
    לכן הדרך הכי טובה ללמוד היא צעד אחר צעד.
    """
}


# --- Semantic Similarity ---

def compute_similarity_simple(text1: str, text2: str) -> float:
    """
    Similarity פשוטה מבוססת על חפיפת מילים (Jaccard).
    פועלת ללא מודל — fallback מהיר.
    """
    import re

    def get_words(text):
        return set(re.findall(r'\b[\w֐-׿]{2,}\b', text.lower()))

    words1 = get_words(text1)
    words2 = get_words(text2)

    if not words1 or not words2:
        return 0.0

    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return round(intersection / union, 3)


def compute_similarity_transformers(text1: str, text2: str) -> Optional[float]:
    """
    Similarity סמנטי עם sentence-transformers.
    מדויק יותר — מבין משמעות ולא רק מילים.
    """
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np

        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        embeddings = model.encode([text1, text2])

        # Cosine similarity
        dot = np.dot(embeddings[0], embeddings[1])
        norm = np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        similarity = float(dot / norm) if norm > 0 else 0.0
        return round(similarity, 3)

    except ImportError:
        return None
    except Exception:
        return None


def get_similarity(text1: str, text2: str) -> Dict:
    """
    מחשב similarity — מנסה transformers, fallback ל-Jaccard.
    """
    transformer_score = compute_similarity_transformers(text1, text2)

    if transformer_score is not None:
        return {
            "score": transformer_score,
            "method": "sentence-transformers",
            "model": "paraphrase-multilingual-MiniLM-L12-v2"
        }
    else:
        jaccard = compute_similarity_simple(text1, text2)
        return {
            "score": jaccard,
            "method": "jaccard",
            "note": "install sentence-transformers for better accuracy"
        }


# --- LLM Reference Generation ---

def get_llm_reference(topic: str, api_key: Optional[str] = None) -> Dict:
    """
    מייצר הסבר אידיאלי לנושא.
    אם יש API Key → קורא ל-Claude/OpenAI.
    אחרת → משתמש ב-reference מוכן מראש.
    """
    api_key = api_key or os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")

    if api_key and api_key.startswith("sk-ant"):
        # Claude API
        try:
            import httpx
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-20240307",
                    "max_tokens": 200,
                    "messages": [{
                        "role": "user",
                        "content": f"הסבר את הנושא '{topic}' בעברית פשוטה לילד בכיתה ז'. השתמש באנלוגיות ודוגמאות. עד 5 משפטים."
                    }]
                },
                timeout=10.0
            )
            if response.status_code == 200:
                text = response.json()["content"][0]["text"]
                return {"text": text, "source": "claude"}
        except Exception:
            pass

    # Fallback — reference מוכן מראש
    topic_lower = topic.lower()
    for key in REFERENCE_EXPLANATIONS:
        if key in topic_lower:
            return {"text": REFERENCE_EXPLANATIONS[key], "source": "reference"}

    return {"text": REFERENCE_EXPLANATIONS["default"], "source": "default"}


# --- Bonus חישוב ---

SIMILARITY_THRESHOLD = 0.20   # מינימום similarity לבונוס (Jaccard scale)
CONCISENESS_BONUS_MAX = 15.0  # בונוס מקסימלי


def compute_conciseness_bonus(
    candidate_text: str,
    reference_text: str,
    similarity: float,
    similarity_threshold: float = SIMILARITY_THRESHOLD
) -> Dict:
    """
    מחשב בונוס תמציתיות:
    - אם similarity > threshold AND קצר יותר → בונוס
    - ככל שקצר יותר ועדיין דומה → בונוס גבוה יותר
    """
    candidate_words = len(candidate_text.split())
    reference_words = len(reference_text.split())

    if reference_words == 0:
        return {"bonus": 0.0, "reason": "reference ריק"}

    length_ratio = candidate_words / reference_words

    if similarity < similarity_threshold:
        return {
            "bonus": 0.0,
            "reason": f"similarity נמוכה מדי ({similarity:.2f} < {similarity_threshold})",
            "candidate_words": candidate_words,
            "reference_words": reference_words,
        }

    if length_ratio >= 1.0:
        return {
            "bonus": 0.0,
            "reason": "ההסבר לא קצר יותר מה-reference",
            "candidate_words": candidate_words,
            "reference_words": reference_words,
            "length_ratio": round(length_ratio, 2),
        }

    # בונוס: ככל שהמועמד קצר יותר ועדיין דומה
    conciseness_factor = 1 - length_ratio          # 0 → 1 (ככל שקצר יותר)
    similarity_factor = min(1.0, similarity / 0.7)  # נורמליזציה

    bonus = CONCISENESS_BONUS_MAX * conciseness_factor * similarity_factor
    bonus = round(min(CONCISENESS_BONUS_MAX, bonus), 2)

    return {
        "bonus": bonus,
        "reason": f"קצר ב-{round((1-length_ratio)*100)}% עם similarity {similarity:.2f}",
        "candidate_words": candidate_words,
        "reference_words": reference_words,
        "length_ratio": round(length_ratio, 2),
        "similarity": similarity,
    }


# --- ניתוח מלא ---

def analyze_with_llm_comparison(
    candidate_text: str,
    topic: str,
    api_key: Optional[str] = None,
) -> Dict:
    """
    ניתוח ELI5 מלא + השוואה ל-LLM reference.
    """
    from nlp.eli5_analyzer import analyze_eli5

    # ניתוח בסיסי
    base_result = analyze_eli5(candidate_text)

    # reference
    reference = get_llm_reference(topic, api_key)

    # similarity
    sim_result = get_similarity(candidate_text, reference["text"])

    # בונוס תמציתיות
    bonus_result = compute_conciseness_bonus(
        candidate_text,
        reference["text"],
        sim_result["score"]
    )

    # ציון סופי עם בונוס
    final_score = min(100.0, base_result["total_score"] + bonus_result["bonus"])

    return {
        "base_score": base_result["total_score"],
        "conciseness_bonus": bonus_result["bonus"],
        "final_score": round(final_score, 2),
        "passes_minimum": final_score >= 60,
        "breakdown": base_result["breakdown"],
        "similarity": sim_result,
        "conciseness_analysis": bonus_result,
        "reference_source": reference["source"],
        "feedback": base_result["feedback"],
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")

    print("LLM Comparator — Demo")
    print("=" * 50)

    examples = [
        {
            "label": "הסבר קצר ומדויק",
            "topic": "סייבר",
            "text": "סייבר זה כמו מנעול על המחשב. דמיין שהמחשב שלך הוא בית — אנשי הסייבר שומרים שאף אחד לא יכנס."
        },
        {
            "label": "הסבר ארוך עם ז'רגון",
            "topic": "סייבר",
            "text": "אבטחת מידע וסייבר עוסקת בהגנה על מערכות מחשוב ממתקפות זדוניות. פרוטוקולי אבטחה כוללים הצפנה, אימות דו-שלבי ובדיקת פגיעויות במערכות המידע."
        },
    ]

    for ex in examples:
        print(f"\n{'='*50}")
        print(f"דוגמה: {ex['label']}")
        result = analyze_with_llm_comparison(ex["text"], ex["topic"])
        print(f"ציון בסיס:     {result['base_score']}/100")
        print(f"בונוס תמציתיות: +{result['conciseness_bonus']}")
        print(f"ציון סופי:     {result['final_score']}/100")
        print(f"Similarity:    {result['similarity']['score']} ({result['similarity']['method']})")
        print(f"Reference:     {result['reference_source']}")
        print(f"ניתוח בונוס:   {result['conciseness_analysis']['reason']}")
