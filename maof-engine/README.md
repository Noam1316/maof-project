# Maof Engine — Dual Scoring Engine

מנוע השיבוץ של מעוף Tech-Lead Israel.

## מה זה

מערכת AI לשיבוץ אופטימלי של חיילים משוחררים עם הוראת STEM וחברות הייטק.  
משלבת Dual Scoring Engine + Hungarian Algorithm לאופטימיזציה גלובלית.

## ארכיטקטורה

```
ציון A (הוראה) + ציון B (חברה) + ציון C (Three-Way)
        ↓
   ציון נפח גיאומטרי: ∛(A-60)×(B-60)×(C-60)
        ↓
   Hungarian Algorithm → שיבוץ גלובלי אופטימלי
```

## מבנה הקוד

```
maof-engine/
├── models/
│   ├── candidate.py     # מודל מועמד מלא
│   ├── school.py        # מודל בית ספר
│   └── company.py       # מודל חברה
├── scoring/
│   ├── score_a.py       # ציון הוראה (ELI5 + מקצוע + שימור + השפעה)
│   ├── score_b.py       # ציון חברה (טכני + צמיחה + רכים + תרבות)
│   ├── score_c.py       # Three-Way Score
│   └── volume.py        # ציון נפח גיאומטרי + ציון סופי
├── matching/
│   └── hungarian.py     # Hungarian Algorithm — scipy
├── data/
│   └── synthetic.py     # Synthetic Data Generator
├── main.py              # מנוע ראשי — הרצת דמו
└── requirements.txt
```

## ציון A — כושר הוראה (0-100)

| מדד | משקל |
|-----|------|
| ELI5 | 35% |
| התאמת מקצוע | 25% |
| שימור (מרחק + משפחה + מחויבות) | 25% |
| השפעה (פריפריה + טיפוח + דחיפות) | 15% |

## ציון B — התאמה לחברה (0-100)

| מדד | משקל |
|-----|------|
| מיומנות טכנית (Tech Test + Stack + רקע) | 35% |
| פוטנציאל צמיחה | 25% |
| כישורים רכים (מנהיגות + צוות + ELI5) | 25% |
| התאמה תרבותית | 15% |

## ציון נפח

```python
נפח = (A - 60) × (B - 60) × (C - 60)
ציון_נפח = ∛נפח ÷ 40 × 100
ציון_סופי = נפח × 0.5 + A × 0.25 + B × 0.25
```

סף מינימום: **60 בכל ציון**. מתחת לסף — לא נכנס לשיבוץ.

## הרצה

```bash
pip install -r requirements.txt
python main.py
```

## פלט דוגמה

```
Maof — Dual Scoring Engine
==================================================
מועמדים: 5 | בתי ספר: 3 | חברות: 3

שיבוצים אופטימליים:
  C005 → S002 + CO001 | ציון: 62.87
  C002 → S003 + CO001 | ציון: 52.81
  C004 → S002 + CO003 | ציון: 47.83
  C001 → S001 + CO003 | ציון: 46.63
  C003 → S001 + CO001 | ציון: 39.91

ערך כולל: 250.05
```

## שלבים הבאים (עם המענק)

- [ ] FastAPI REST API
- [ ] Database (PostgreSQL/Supabase)
- [ ] NLP אמיתי לELI5 (sentence-transformers)
- [ ] Google Maps API לחישוב מרחק
- [ ] Genetic Algorithm לכיוון משקלות
- [ ] Feedback Loop

---

*נועם אוקון — מעוף Tech-Lead Israel | 2026*
