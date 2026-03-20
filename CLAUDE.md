# מיזם מעוף – Tech-Lead Israel

## סקירה כללית
מיזם **מעוף** הוא מערכת AI לתמיכת החלטה (DSS) לניהול הון אנושי וגיוס מומחי STEM למערכת החינוך, במודל קריירה מעגלית. המיזם מחבר בין לוחמים משוחררים מצה"ל לתוכנית "לוחמים להייטק" של האגף.

**יוצר המיזם:** נעם — בעל רקע מבצעי-טכנולוגי בצה"ל (מנהל רשת + חמ"ליסט). בונה את המיזם כ-one-person operation עם Claude Code כשותף פיתוח מרכזי.

**מטרת-על:** להפוך את מעוף למיזם ממומן (בקשת מענק רשות החדשנות — מסלול תנופה), עם demo חי שמדגים יכולת טכנולוגית.

---

## הבעיה שמעוף פותר

| צד | בעיה |
|----|------|
| **מערכת החינוך** | מחסור של ~3,500 מורי STEM בישראל |
| **תעשיית ההייטק** | קושי בגיוס ג'וניורים איכותיים |
| **חיילים משוחררים** | מעבר קשה לחיים האזרחיים ללא מסלול ברור |

**הפתרון:** מודל 2+2 מחזורי עם AI שפותר את שלוש הבעיות בו-זמנית.

---

## מסלול 2+2 (The 2+2 Journey)

| שלב | תוכן | פרטים |
|-----|------|--------|
| הכשרה | קורס AI & Data Science | בנאיה קולג', במימון קרן לחיילים משוחררים |
| תחנה א' – תרומה | 2 שנות הוראת STEM | סייבר, פייתון, פיזיקה / חוזה אישי / שכר ~15,000 ש"ח |
| תחנה ב' – תעשייה | 2 שנות הייטק מובטחות | חברות מאמצות: Microsoft, Elbit, Checkpoint |
| ערך מוסף | Seniority Leap | שנתיים הוראה = 18 חודשי ניסיון מקצועי (פיתוח/ניהול, Soft Skills, הדרכה, הובלת פרויקטים) |

**קהל יעד:** לוחמים משוחררים מצה"ל (ראשוני), הורחב גם לחיילים עם רקע מקצועי קודם.

---

## מנוע הדירוג והסינון (Dual Scoring Engine)

מודל דירוג כפול – ציון נפרד לכל צד של הפלטפורמה:

### ציון A: התאמה לבית ספר (School Match) – 100 נקודות

| מדד | משקל | מה נמדד |
|-----|------|---------|
| כושר הוראה (Teaching Aptitude) | 35% | מבחן ELI5 + יכולת תקשורת + ניסיון הדרכה |
| התאמה מקצועית (Subject Match) | 25% | התאמה בין מומחיות המועמד לצורך ביה"ס |
| שימור (Retention Score) | 25% | מרחק מגורים + מצב משפחתי + מחויבות |
| Impact | 15% | עדיפות פריפריה + מדד טיפוח + דחיפות |

### ציון B: התאמה לחברה (Company Match) – 100 נקודות

| מדד | משקל | מה נמדד |
|-----|------|---------|
| מיומנות טכנית (Tech Skills) | 35% | Tech-Stack Match + מבחן STEM מעשי + רקע צבאי טכני |
| פוטנציאל צמיחה (Growth Potential) | 25% | קצב למידה + פסיכומטרי + מסלול קריירה |
| כישורים רכים (Soft Skills) | 25% | ELI5 + מנהיגות + עבודת צוות |
| התאמה תרבותית (Cultural Fit) | 15% | גודל חברה + סגנון עבודה + העדפות מיקום |

### ציון שיבוץ (Placement Score)
- שילוב משוקלל של ציון A + ציון B
- סף מינימום: לפחות 60 בכל ציון (לא משבצים מועמד חזק בהייטק אם הוא חלש בהוראה)
- אופטימיזציה: מקסום ערך כולל לפלטפורמה

### Feedback Loop
- איסוף משוב מביה"ס (דירוג תלמידים, נוכחות, שביעות רצון מנהל)
- איסוף משוב מהחברה (ביצועים, קצב התקדמות, שביעות רצון מנהל)
- השוואת ציון חיזוי vs ביצועים בפועל → עדכון משקלות אוטומטי

---

## המודל הכלכלי (The Budgeting Engine)

| פריט | פרטים |
|------|--------|
| מענק חתימה | עד 45,000 ש"ח בפריפריה (לשנתיים) |
| סבסוד דיור (ת"א/ביקוש) | 2,200 ש"ח לחודש |
| מימון משותף | תקציב גפ"ן 100% להוראה / חברה מאמצת משלמת בנפרד על 50% הייטק |

## ה-Business Case

| צד | ערך |
|----|-----|
| **הבעיה** | מחסור ב-3,500 מורי STEM + קושי בגיוס ג'וניורים איכותיים להייטק |
| **הפתרון** | מודל 2+2 מחזורי עם AI |
| **ROI למדינה** | מענק חתימה נמוך (20k) + צמצום פערים בפריפריה ובת"א |
| **Revenue** | עמלות השמה (35k לעובד) + דמי ניהול SaaS לממשלה |

---

## מבנה הפרויקט הטכני

```
maof-project/
├── signal-news-demo/        # *** הפרויקט הפעיל *** — דמו מודיעין גיאופוליטי
├── פורטל חיילים 2/          # פורטל לחיילים משוחררים (אב-טיפוס)
├── פורטל חיילים 3/          # גרסה 3 של פורטל חיילים (אב-טיפוס)
├── פורטל חברות 2/           # פורטל לחברות הייטק מאמצות (אב-טיפוס)
└── פורטל משרד החינוך 6/     # פורטל למשרד החינוך (אב-טיפוס)
```

### הפורטלים (אב-טיפוסים)
- **פורטל חיילים** — מועמדים נרשמים, עוברים מבחנים, רואים שיבוצים
- **פורטל חברות** — חברות הייטק (Microsoft, Elbit, Checkpoint) צופות במועמדים, מאשרות שיבוצים
- **פורטל משרד החינוך** — מנהלי בתי ספר מגדירים צרכים, צופים במועמדים מותאמים

### Signal News Demo
הדמו הטכנולוגי — פלטפורמת מודיעין גיאופוליטי בזמן אמת שמדגימה:
- יכולת AI לניתוח נתונים ממקורות מרובים (28+ RSS feeds)
- זיהוי אנומליות וסיגנלים (shock detection)
- השוואת תחזיות מול שוקי הימורים (Signal vs Polymarket)
- ניתוח הטיה תקשורתית (Media Bias)
- הכל ללא API keys — keyword-based analysis בלבד

**ראה `signal-news-demo/CLAUDE.md` לכללי פיתוח טכניים.**

---

## Signal News — ארכיטקטורה מלאה

### Flow
```
RSS Sources (28+) → article-cache.ts (in-memory shared cache)
  ├→ ai-analyzer.ts — keyword-based: topics, sentiment, signal/noise, political leaning
  ├→ story-clusterer.ts — groups articles into stories, calculates likelihood
  ├→ shock-detector.ts — statistical anomaly detection (3 shock types)
  ├→ polymarket.ts — Polymarket Gamma API + match stories → alpha detection
  └→ media-bias.ts — 35+ source bias DB + coverage gaps + narrative divergence
```

### Dashboard (4 sections)
1. **Brief** — סיכום מודיעיני יומי + HeroBar עם סטטיסטיקות חיות
2. **Shocks** — זיהוי זעזועים סטטיסטיים (likelihood shocks, narrative splits, fragmentation)
3. **Map + Entities** — מפת עולם SVG + גרף ישויות (NER), בטאבים
4. **Intel Hub** — 4 טאבים: Overview (סטטיסטיקות), Signal vs Market, Media Bias, Live Feed

### Signal vs Market (פיצ'ר מרכזי)
- מושך 50 שווקים פעילים מ-Polymarket Gamma API (ללא מפתח)
- מתאים כתבות לשווקים לפי keyword matching (TOPIC_KEYWORDS — 13 קטגוריות)
- מחשב Alpha Score: `min(100, absDelta * 0.8 + volumeWeight + bestScore * 2)`
- מציג הסבר אוטומטי למה Signal חושב אחרת מהשוק
- Fallback events כש-API לא זמין

### Media Bias Analysis
- DB של 35+ מקורות עם BiasRating (far-left → far-right) ו-FactualRating
- מזהה Coverage Gaps — נושאים שמכוסים רק בצד אחד של הספקטרום
- מזהה Narrative Divergence — אותו נושא מוצג אחרת ע"י שמאל vs ימין

### טכנולוגיות
- Next.js 16 (App Router) + TypeScript + Tailwind CSS v4 + React 19
- Vercel serverless (no DB, no native modules)
- RTL-first (Hebrew), bilingual UI (he/en toggle)

---

## תוכניות עתידיות

### n8n Full-Text Scraping (מתוכנן, לא יושם)
- בעיה: סיווג פוליטי לפי מקור בלבד (כל מאמר ב-Ynet = "center")
- פתרון: n8n ישלוף טקסט מלא → webhook → keyword analyzer משופר על תוכן
- שילוב: 40% source-based + 60% content-based
- קובץ תוכנית מפורט: `.claude/plans/linked-fluttering-puddle.md`

---

## Deployment

- **Signal News Live:** https://signal-news-noam1316s-projects.vercel.app/dashboard
- **GitHub:** https://github.com/Noam1316/signal-news
- **APIs:** Polymarket Gamma API (public), RSS feeds (public) — no keys needed

---

## הערות לפיתוח

IMPORTANT: Rules for working in this codebase:
- Primary UI language: Hebrew (RTL). Always use `dir={dir}` from `useLanguage()`.
- The active demo project is `signal-news-demo/` — see its own CLAUDE.md for technical details.
- Portal directories (פורטל חיילים, פורטל חברות, פורטל משרד החינוך) are earlier prototypes — do not modify without explicit request.
- The Scoring Engine described above is the business logic spec — implementation lives in `signal-news-demo/src/services/`.
- No Anthropic API key available — all analysis must be keyword-based.
- Deployment target: Vercel serverless. No native modules (no better-sqlite3, no sharp custom builds).
- Signal vs Market is the priority feature — don't neglect it when adding other features.
- Prefer clean, minimal UI — less sections with rich content over many sparse sections.
- SectionNav has exactly 4 items — do not add more without explicit request.
- IntelHub uses tabs — add new intel features as tabs, not new dashboard sections.
- `npm run build` MUST pass before push.
