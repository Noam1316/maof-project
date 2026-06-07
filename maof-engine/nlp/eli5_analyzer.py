"""
ELI5 Analyzer — NLP לניתוח יכולת הסבר
מעוף Tech-Lead Israel

מנתח טקסט לפי 6 מדדים:
  1. פשטות      — Flesch-like + אורך מילים ומשפטים
  2. אנלוגיות   — זיהוי "כמו", "דמיין", "זה דומה ל" + איכות + רלוונטיות לנושא
  3. נרטיב      — Hook (חזק/חלש) + מסקנה + בונוס שאלות רטוריות (ציון רציף)
  4. קוהרנטיות  — מילות חיבור + לכידות לקסיקלית + עומק סיבתי (causal chains)
  5. תמציתיות   — פחות מילים לאותו רעיון + TTR + filler detection
  6. דיוק       — כיסוי מושגי ליבה עם fuzzy Hebrew stem matching

ללא API Key — keyword-based analysis בלבד.
"""

import re
import math
import os
from typing import Dict, List, Optional


# ─── Sentence Transformer — lazy loader ──────────────────────────────────────
_ST_MODEL = None
_ST_AVAILABLE: Optional[bool] = None


def _get_st_model():
    global _ST_MODEL, _ST_AVAILABLE
    if _ST_AVAILABLE is None:
        try:
            from sentence_transformers import SentenceTransformer
            _ST_MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            _ST_AVAILABLE = True
        except Exception:
            _ST_AVAILABLE = False
    return _ST_MODEL if _ST_AVAILABLE else None


def _semantic_cohesion(sentences: List[str]) -> float:
    if len(sentences) < 2:
        return 0.5

    model = _get_st_model()
    if model is not None:
        try:
            from sentence_transformers import util
            embeddings = model.encode(sentences, convert_to_tensor=True, show_progress_bar=False)
            scores = []
            for i in range(len(sentences) - 1):
                sim = util.cos_sim(embeddings[i], embeddings[i + 1]).item()
                scores.append((sim + 1.0) / 2.0)
            return sum(scores) / len(scores)
        except Exception:
            pass

    return _lexical_cohesion(sentences)


# ─── Dynamic CONCEPT_MAP — Groq fallback לנושאים לא ידועים ──────────────────
_DYNAMIC_CONCEPTS: Dict[str, List[str]] = {}


def _fetch_concepts_for_topic(topic: str) -> List[str]:
    topic_norm = topic.strip().lower()
    if topic_norm in _DYNAMIC_CONCEPTS:
        return _DYNAMIC_CONCEPTS[topic_norm]

    groq_key = os.getenv("GROQ_API_KEY", "")
    if not groq_key:
        _DYNAMIC_CONCEPTS[topic_norm] = []
        return []

    try:
        import httpx, json as _json

        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return ONLY a JSON array of 8-12 simple keyword strings "
                        "that a good ELI5 explanation of the given topic MUST include. "
                        "Use concrete, non-jargon words. "
                        'Example for "electricity": ["wire","flow","switch","light","charge","circuit"]. '
                        "Return ONLY the JSON array, no other text."
                    ),
                },
                {"role": "user", "content": f"Topic: {topic}"},
            ],
            "max_tokens": 120,
            "temperature": 0.1,
        }
        resp = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=5.0,
        )
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"].strip()
            concepts = _json.loads(content)
            if isinstance(concepts, list) and concepts:
                _DYNAMIC_CONCEPTS[topic_norm] = [str(c).lower() for c in concepts]
                return _DYNAMIC_CONCEPTS[topic_norm]
    except Exception:
        pass

    _DYNAMIC_CONCEPTS[topic_norm] = []
    return []


# --- מילות אנלוגיה ---
ANALOGY_KEYWORDS_HE = [
    "כמו", "דמיין", "דמיינו", "זה דומה ל", "בדיוק כמו",
    "תחשוב על", "תחשבו על", "לדוגמה", "למשל", "נגיד",
    "נניח", "נדמה", "משל", "דומה ל", "בדומה ל",
    "זה כאילו", "כאילו", "כאלו", "ממש כמו",
]

ANALOGY_KEYWORDS_EN = [
    "like", "imagine", "just like", "similar to", "think of",
    "for example", "for instance", "such as", "as if",
    "picture", "consider", "suppose", "say you", "pretend",
]

# --- מילות חיבור (קוהרנטיות) ---
COHERENCE_KEYWORDS_HE = [
    "לכן", "כי", "בגלל", "אז", "לפיכך", "כתוצאה",
    "ראשית", "שנית", "לסיום", "בנוסף", "יתרה מזאת",
    "לעומת זאת", "אם כן", "מכאן ש",
]

COHERENCE_KEYWORDS_EN = [
    "therefore", "because", "so", "thus", "hence", "first",
    "second", "finally", "additionally", "moreover", "however",
    "in conclusion", "as a result", "for this reason",
]

# --- Hook keywords ---
HOOK_KEYWORDS_HE = [
    "דמיין", "דמיינו", "תחשוב", "תחשבו", "נניח", "נגיד",
    "שאלה", "למה", "איך", "האם ידעת",
    "בוא נגיד", "בואו נגיד", "חשבת פעם",
]
HOOK_KEYWORDS_EN = [
    "imagine", "suppose", "picture", "have you ever", "why does",
    "what if", "let's say", "did you know", "ever wonder", "think about",
]

# Hook חזק — מזמין ויזואליזציה אקטיבית (מקבל 50 נק', לעומת 35 ל-hook חלש)
STRONG_HOOK_HE = ["דמיין", "דמיינו", "תחשוב", "תחשבו", "חשבת פעם", "בוא נגיד", "בואו נגיד"]
STRONG_HOOK_EN = ["imagine", "picture", "have you ever", "ever wonder", "think about"]

# --- Conclusion keywords ---
CONCLUSION_KEYWORDS_HE = [
    "לכן", "לסיכום", "לסיום", "מכאן ש",
    "לפיכך", "ולכן", "כלומר", "בקצרה", "בגדול",
    "אז בעצם", "זאת אומרת",
]
CONCLUSION_KEYWORDS_EN = [
    "therefore", "in conclusion", "so basically", "in short",
    "the bottom line", "to summarize", "in other words",
    "ultimately", "that's why", "which means",
]

# --- Causal chain patterns — מסביר *למה* לא רק *מה* ---
CAUSAL_PATTERNS_HE = [
    "בגלל ש", "גורם ל", "מאפשר ל", "כתוצאה", "הסיבה ש",
    "מה שאומר", "מה שמשמעו", "מכאן ש", "זה אומר ש",
]
CAUSAL_PATTERNS_EN = [
    "because of", "causes", "enables", "as a result", "the reason",
    "which means", "therefore", "leads to", "that's why",
]

# --- מילות מילוי (filler) ---
FILLER_PHRASES_HE = [
    "כמובן", "בגדול", "למעשה", "כאמור", "כידוע", "בין היתר",
    "מן הסתם", "אחרי הכל", "בסופו של דבר", "חשוב לציין",
    "כדאי לציין", "ראוי לציין", "מעניין לציין",
]

FILLER_PHRASES_EN = [
    "basically", "obviously", "needless to say", "as mentioned",
    "it is worth noting", "it goes without saying", "first and foremost",
    "last but not least", "at the end of the day",
]

# --- מפת מושגי ליבה לפי נושא ---
CONCEPT_MAP: Dict[str, List[str]] = {
    "סייבר":      ["הגנה", "מנעול", "בית", "סיסמה", "פריצה", "גנב", "אבטחה", "מגן",
                   "security", "protection", "password", "hack", "lock", "threat"],
    "פייתון":     ["מתכון", "הוראות", "שפה", "מחשב", "תכנות", "קוד", "שורה",
                   "code", "recipe", "instructions", "language", "program"],
    "רשתות":      ["כביש", "חיבור", "נתונים", "תקשורת", "כתובת", "נתב",
                   "connection", "network", "address", "router", "data"],
    "ai":         ["מוח", "למידה", "דפוסים", "ניסיון", "זיהוי", "תגמול",
                   "learn", "pattern", "brain", "recognize", "train"],
    "ענן":        ["שרת", "אחסון", "מרחוק", "גיבוי", "ספרייה", "אינטרנט",
                   "server", "storage", "remote", "backup", "cloud"],
    "אלגוריתמים": ["שלבים", "סדר", "חיפוש", "מיון", "פתרון", "בעיה",
                   "steps", "order", "search", "sort", "solution"],
    "web":        ["דף", "כתובת", "קישור", "שרת", "בקשה", "תגובה",
                   "page", "url", "link", "request", "response"],
    "מתמטיקה":   ["מספרים", "חשבון", "לספור", "פעולה", "חיבור", "חיסור", "תוצאה",
                   "numbers", "count", "calculation", "add", "subtract"],
    "פיזיקה":    ["כוח", "תנועה", "אנרגיה", "מסה", "מהירות", "כובד", "גל", "חשמל",
                   "force", "motion", "energy", "mass", "speed", "gravity", "wave"],
    "כימיה":     ["אטום", "מולקולה", "תגובה", "חומר", "אלקטרון", "קשר", "מתכת",
                   "atom", "molecule", "reaction", "element", "electron", "bond"],
    "ביולוגיה":  ["תא", "גוף", "חיים", "DNA", "גן", "אבולוציה", "אורגניזם", "מערכת",
                   "cell", "body", "life", "gene", "evolution", "organism"],
    "כלכלה":     ["כסף", "שוק", "מחיר", "ביקוש", "היצע", "צמיחה", "אינפלציה",
                   "money", "market", "price", "demand", "supply", "growth"],
    "ניהול":     ["צוות", "מטרה", "תוכנית", "אחריות", "תקשורת", "החלטה", "משאבים",
                   "team", "goal", "plan", "responsibility", "decision", "resources"],
    "מחשב":      ["עיבוד", "זיכרון", "קלט", "פלט", "חישוב", "מעבד", "נתונים",
                   "process", "memory", "input", "output", "cpu", "data"],
}

# --- מילים ז'רגוניסטיות ---
JARGON_HE = [
    "אלגוריתם", "פרמטר", "מטריקס", "פרוטוקול", "ממשק",
    "אינטגרציה", "מודול", "דאטה", "ביג דאטה", "מל",
]

JARGON_EN = [
    "algorithm", "parameter", "matrix", "protocol", "interface",
    "integration", "module", "dataset", "machine learning",
    "neural network", "gradient", "epoch", "tensor",
]


def tokenize(text: str) -> List[str]:
    words = re.findall(r'\b[\w֐-׿]+\b', text)
    return [w for w in words if len(w) > 1]


def split_sentences(text: str) -> List[str]:
    sentences = re.split(r'[.!?。]\s*', text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]


# --- מדד 1: פשטות ---
def simplicity_score(text: str) -> float:
    words = tokenize(text)
    sentences = split_sentences(text)

    if not words or not sentences:
        return 50.0

    avg_word_len = sum(len(w) for w in words) / len(words)
    avg_sentence_len = len(words) / len(sentences)

    word_score = max(0, 100 - (avg_word_len - 4) * 15)
    sentence_score = max(0, 100 - abs(avg_sentence_len - 12) * 5)

    all_jargon = JARGON_HE + JARGON_EN
    text_lower = text.lower()
    jargon_count = sum(1 for j in all_jargon if j.lower() in text_lower)
    jargon_penalty = min(40, jargon_count * 10)

    score = (word_score * 0.4 + sentence_score * 0.6) - jargon_penalty
    return round(max(0, min(100, score)), 2)


def _keyword_in_real_context(keyword: str, sentences: List[str], min_words: int = 6) -> bool:
    kw_lower = keyword.lower()
    for sentence in sentences:
        if kw_lower in sentence.lower() and len(sentence.split()) >= min_words:
            return True
    return False


# --- מדד 2: אנלוגיות (עם בדיקת רלוונטיות לנושא) ---
def analogy_score(text: str, topic: str = "") -> float:
    """
    מדד האנלוגיות — איכות × כמות × רלוונטיות לנושא.

    רלוונטיות: אם יש נושא ידוע, משפט אנלוגי שלא מכיל מילת domain
    מקבל 60% מציון האיכות (אנלוגיה יצירתית > אנלוגיה לא רלוונטית).
    """
    sentences = split_sentences(text)
    all_keywords = ANALOGY_KEYWORDS_HE + ANALOGY_KEYWORDS_EN

    # מילות domain לבדיקת רלוונטיות — stem של 4 תווים לעמידות מורפולוגית
    topic_norm = topic.strip().lower()
    domain_stems: List[str] = []
    if topic_norm:
        for key, vals in CONCEPT_MAP.items():
            if key in topic_norm or topic_norm in key:
                domain_stems = [v[:4] for v in vals if len(v) >= 4]
                break

    analogy_sentences = []
    used_keywords: set = set()
    for sent in sentences:
        sent_lower = sent.lower()
        for kw in all_keywords:
            if kw.lower() in sent_lower and len(sent.split()) >= 6:
                analogy_sentences.append((sent, _is_domain_relevant(sent_lower, domain_stems)))
                used_keywords.add(kw)
                break

    if not analogy_sentences:
        return 20.0

    def _sentence_quality(s: str, relevant: bool) -> float:
        w = len(s.split())
        if w >= 15:  base = 95.0
        elif w >= 10: base = 75.0
        else:         base = 55.0
        # אנלוגיה לא רלוונטית לנושא מקבלת 60% מהציון
        return base if relevant else base * 0.6

    avg_quality = sum(_sentence_quality(s, r) for s, r in analogy_sentences) / len(analogy_sentences)

    diversity_bonus = 10.0 if len(used_keywords) >= 2 else 0.0
    count_bonus = min(12.0, (len(analogy_sentences) - 1) * 6)

    return min(100.0, avg_quality + diversity_bonus + count_bonus)


def _is_domain_relevant(sent_lower: str, domain_stems: List[str]) -> bool:
    """True אם המשפט מכיל לפחות מילת domain אחת (stem match), או אם אין domain ידוע."""
    if not domain_stems:
        return True
    return any(stem in sent_lower for stem in domain_stems)


# --- מדד 3: מבנה נרטיבי — ציון רציף במקום 4 ערכים ---
def creativity_score(text: str) -> float:
    """
    Hook (חזק/חלש) + מסקנה + בונוס שאלות רטוריות לאורך הטקסט.

    hook חזק (דמיין, תחשוב)  → 50 נק'
    hook חלש (נגיד, למה)     → 35 נק'
    מסקנה                    → 40 נק'
    שאלה רטורית אחרי משפט 1 → עד 10 נק'
    בסיס ללא כלום            → 20 נק'
    """
    words = text.split()
    if not words:
        return 20.0

    sentences = split_sentences(text)
    first = " ".join(words[:30]).lower()
    last  = " ".join(words[-40:]).lower()

    # Hook score (0-50)
    if any(k.lower() in first for k in STRONG_HOOK_HE + STRONG_HOOK_EN):
        hook_score = 50
    elif any(k.lower() in first for k in HOOK_KEYWORDS_HE + HOOK_KEYWORDS_EN):
        hook_score = 35
    else:
        hook_score = 0

    # Conclusion score (0-40)
    conclusion_score = 40 if any(
        k.lower() in last for k in CONCLUSION_KEYWORDS_HE + CONCLUSION_KEYWORDS_EN
    ) else 0

    # בונוס שאלות רטוריות אחרי המשפט הראשון (0-10)
    middle = " ".join(sentences[1:]) if len(sentences) > 1 else ""
    q_bonus = min(10, middle.count("?") * 5)

    total = hook_score + conclusion_score + q_bonus
    return round(max(20.0, min(100.0, total)), 2)


# --- עזר: לכידות לקסיקלית ---
def _lexical_cohesion(sentences: List[str]) -> float:
    if len(sentences) < 2:
        return 0.5
    scores = []
    for i in range(len(sentences) - 1):
        s1 = {w.lower() for w in sentences[i].split()     if len(w) > 2}
        s2 = {w.lower() for w in sentences[i + 1].split() if len(w) > 2}
        if not s1 or not s2:
            scores.append(0.0)
            continue
        scores.append(len(s1 & s2) / len(s1 | s2))
    return sum(scores) / len(scores) if scores else 0.0


# --- מדד 4: קוהרנטיות + עומק סיבתי ---
def coherence_score(text: str) -> float:
    """
    שלושה מרכיבים:
      1. מילות חיבור לוגיות  — מקסימום 35 נק'
      2. לכידות לקסיקלית     — מקסימום 35 נק'
      3. עומק סיבתי          — causal chains ("בגלל ש", "גורם ל"...) — מקסימום 30 נק'

    עומק סיבתי מבחין בין "מה" ל-"למה" — תנאי מפתח ב-ELI5 אמיתי.
    """
    text_lower = text.lower()
    sentences = split_sentences(text)

    if len(sentences) < 2:
        return 40.0

    # --- מרכיב 1: מילות חיבור (מקסימום 35 נק') ---
    all_coherence = COHERENCE_KEYWORDS_HE + COHERENCE_KEYWORDS_EN
    found = sum(1 for kw in all_coherence if kw.lower() in text_lower)
    connective_score = min(35, found * 9)

    # --- מרכיב 2: לכידות סמנטית (מקסימום 35 נק') ---
    cohesion = _semantic_cohesion(sentences)
    lexical_score = min(35, cohesion * 210)

    # --- מרכיב 3: עומק סיבתי (מקסימום 30 נק') ---
    all_causal = CAUSAL_PATTERNS_HE + CAUSAL_PATTERNS_EN
    causal_count = sum(1 for p in all_causal if p.lower() in text_lower)
    causal_score = min(30, causal_count * 12)

    return round(min(100, connective_score + lexical_score + causal_score), 2)


# --- מדד 5: תמציתיות ---
def conciseness_score(text: str) -> float:
    from collections import Counter
    words = tokenize(text)

    if not words:
        return 50.0

    word_counts = Counter(w.lower() for w in words if len(w) > 3)
    repetitions = sum(1 for count in word_counts.values() if count > 2)
    repetition_penalty = min(30, repetitions * 10)

    length_penalty = 0
    if len(words) < 20:
        length_penalty = 20
    elif len(words) > 150:
        length_penalty = 15

    ttr_penalty = 0
    if len(words) > 15:
        ttr = len(set(w.lower() for w in words)) / len(words)
        if ttr < 0.35:
            ttr_penalty = min(25, int((0.35 - ttr) * 80))

    text_lower = text.lower()
    all_fillers = FILLER_PHRASES_HE + FILLER_PHRASES_EN
    filler_count = sum(1 for f in all_fillers if f.lower() in text_lower)
    filler_penalty = min(15, filler_count * 5)

    score = 100 - length_penalty - repetition_penalty - ttr_penalty - filler_penalty
    return round(max(0, min(100, score)), 2)


# --- עזר: fuzzy Hebrew stem matching ---
def _concept_covered(concept: str, text_lower: str) -> bool:
    """
    4-char prefix match — מתמודד עם נטיות עברית (מנעול/מנעולים/מנעולי).
    מילים קצרות (<4 תווים) נבדקות כمطابقה מלאה.
    """
    if len(concept) >= 4:
        return concept[:4] in text_lower
    return concept in text_lower


# --- מדד 6: דיוק (עם fuzzy matching) ---
def accuracy_score(text: str, topic: str = "") -> float:
    """
    כיסוי מושגי ליבה עם fuzzy stem matching לעמידות מורפולוגית בעברית.
    "מנעולים" ו-"מנעול" שניהם יספרו ככיסוי של "מנעול".
    """
    words = tokenize(text)
    text_lower = text.lower()

    if not words:
        return 0.0

    topic_norm = topic.strip().lower()
    if topic_norm:
        concepts: List[str] = []
        for key, vals in CONCEPT_MAP.items():
            if key in topic_norm or topic_norm in key:
                concepts = vals
                break

        if not concepts:
            concepts = _fetch_concepts_for_topic(topic)

        if concepts:
            covered = sum(1 for c in concepts if _concept_covered(c, text_lower))
            coverage = covered / len(concepts)
            base = min(100.0, coverage * 230 + 30)
            length_penalty = 20 if len(words) < 20 else 0
            return round(max(0, base - length_penalty), 2)

    # בלי topic: ציון סובסטנס
    content_words = [w for w in words if len(w) > 3]
    if not content_words:
        return 30.0

    unique_content = len(set(w.lower() for w in content_words))
    density = unique_content / len(content_words)

    word_count = len(words)
    if   word_count < 10:  length_cap = 40
    elif word_count < 20:  length_cap = 65
    elif word_count < 30:  length_cap = 80
    else:                  length_cap = 100

    return round(min(float(length_cap), density * 110), 2)


# --- ציון ELI5 מלא ---
def analyze_eli5(text: str, topic: str = "") -> Dict:
    if not text or len(text.strip()) < 10:
        return {
            "total_score": 0.0,
            "passes_minimum": False,
            "breakdown": {},
            "feedback": ["הטקסט קצר מדי לניתוח"]
        }

    simplicity   = simplicity_score(text)
    analogies    = analogy_score(text, topic)        # topic מועבר לבדיקת רלוונטיות
    narrative    = creativity_score(text)
    coherence    = coherence_score(text)
    conciseness  = conciseness_score(text)
    accuracy     = accuracy_score(text, topic)

    total = (
        simplicity  * 0.25 +
        analogies   * 0.25 +
        narrative   * 0.15 +
        coherence   * 0.15 +
        accuracy    * 0.10 +
        conciseness * 0.10
    )
    total = round(total, 2)

    feedback = []
    if simplicity < 60:
        feedback.append("השתמש במילים פשוטות יותר, הימנע מז'רגון")
    if analogies < 60:
        feedback.append("הוסף אנלוגיות רלוונטיות לנושא — 'זה כמו...', 'דמיין ש...'")
    if narrative < 60:
        feedback.append("פתח עם הזמנה חזקה ('דמיין ש...') וסיים עם מסקנה ('לכן', 'כלומר')")
    if coherence < 60:
        feedback.append("הוסף הסבר סיבתי — 'בגלל ש', 'גורם ל', 'מה שאומר ש'")
    if accuracy < 50:
        feedback.append("הסבר שטחי — הוסף פרטים ממשיים על הנושא")
    if conciseness < 60:
        feedback.append("נסה לקצר — פחות מילים לאותו רעיון")

    return {
        "total_score": total,
        "passes_minimum": total >= 60,
        "breakdown": {
            "simplicity":          simplicity,
            "analogies":           analogies,
            "narrative_structure": narrative,
            "coherence":           coherence,
            "accuracy":            accuracy,
            "conciseness":         conciseness,
        },
        "feedback": feedback if feedback else ["הסבר טוב! המשך כך"]
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")

    examples = [
        {
            "label": "הסבר טוב — hook חזק + אנלוגיה רלוונטית + סיבתיות",
            "topic": "סייבר",
            "text": """
            דמיין שיש לך בית עם דלת ומנעול. הסיסמה שלך היא המפתח.
            כשגנב מנסה לפרוץ, המנעול הדיגיטלי מתנגד — בגלל שהאבטחה
            יוצרת חומת הגנה שקשה לפרוץ אותה. זה כמו שוטר שעומד בדלת
            ומוודא שרק אתה יכול להיכנס. לכן, סיסמה חזקה היא הבסיס לכל הגנה.
            """
        },
        {
            "label": "הסבר רע — ז'רגון, אנלוגיה לא רלוונטית",
            "topic": "סייבר",
            "text": """
            המחשב מבצע אופרציות בינאריות על ידי טרנזיסטורים. זה כמו
            שאנחנו אוהבים ללכת לים בקיץ. הפרוטוקול מבצע אינסטרוקציות
            מהמחסנית על ידי שימוש ב-ALU וב-control unit.
            """
        },
    ]

    for ex in examples:
        print(f"\n{'='*55}")
        print(f"דוגמה: {ex['label']}")
        print(f"{'='*55}")
        result = analyze_eli5(ex["text"], ex.get("topic", ""))
        print(f"ציון כולל: {result['total_score']}/100  (עובר: {'✅' if result['passes_minimum'] else '❌'})")
        for k, v in result["breakdown"].items():
            print(f"  {k:<22}: {v}")
        print(f"משוב: {result['feedback']}")
