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
| פוטנציאל צמיחה (Growth Potential) | 25% | קצב למידה + רקע אקדמי/יחידה + מסלול קריירה |
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

## מנוע מעוף — Backend חי (maof-engine/)

> **המנוע ממומש ועובד בפועל** — לא עוד spec. FastAPI על Render, מחובר ל-Supabase, עם Groq לדירוג LLM ו-fallback היוריסטי בכל מקום.

### Stack
- FastAPI + Pydantic · Python 3.11 · uvicorn
- Supabase (Postgres) דרך REST — ישויות כ-JSONB, fallback in-memory אם אין env
- Groq (`llama-3.3-70b-versatile`) לדירוג; **מכסה: 100K טוקנים/יום (free)** — כשנגמרת, דירוג נופל ל-heuristic בשקט
- Deploy: Render (free) — keep-alive דרך `.github/workflows/keep-alive.yml` (פינג /health כל 10 דק'; GitHub cron לא 100% אמין — חמם ידנית לפני דמו)

### Endpoints מרכזיים (api/routes.py — 30+)
- `/score`, `/score/breakdown`, `/score/company` (score_b אמיתי לפי candidate_id), `/score/whatif`, `/recommend`, `/match` (Hungarian)
- `/candidates` · `/schools` · `/companies` · `/placements` — CRUD על Supabase
- `/eli5*` — דירוג ELI5 (ציון A) · `/chat` — proxy ל-Groq
- `/tech/logic/*` (שכבה 1) · `/code/test*` (שכבה 2) · `/tech/architecture/*` (שכבה 3)
- `/feedback/*` — Feedback Loop

### המבחן הטכני — 3 שכבות (מזין ציון B)
| שכבה | מודול | מודד | מזין רכיב |
|------|-------|------|-----------|
| 1 · הגיון בשפה זרה | `nlp/logic_test.py` | מהירות למידה (קוד בשפה מומצאת, חוקים inline) | Growth Potential |
| 2 · מבחן קוד אדפטיבי | `nlp/code_test.py` | עומק טכני (5 רמות, must-pass-to-advance) | Tech Skills |
| 3 · ארכיטקטורה | `nlp/architecture_test.py` | חשיבה מערכתית (כיסוי **רובריקה**, לא דמיון ל-AI) | Tech Skills/Systemic |

- UI: פורטל `tech-test/` — `tech_test_score = code×0.45 + architecture×0.30 + logic×0.25`
- ב-`score_b.py`: `tech_skills = code×0.6 + systemic×0.4` (fallback `tech_test_score`); `growth_potential` מקפל `logic_score×0.30` כשקיים (אחרת proxy מקורי)
- שדות מועמד: `eli5_score` (ציון A) · `logic_score` · `code_score` · `systemic_score` · `tech_test_score`

### הלולאה המלאה (E2E — עובדת, נבדקה)
```
רישום בפורטל חיילים → POST /candidates (Supabase)
  → מבחן ELI5 (ציון A) + מבחן טכני 3 שכבות (ציון B)
  → המועמד מופיע חי בפורטל חינוך + חברות עם score_b אמיתי
  → שיבוץ בלחיצה → נשמר ב-Supabase → נראה בכל הפורטלים
```
כל מועמד נושא `candidate_id` דרך URL + localStorage. הפרופיל בפורטל חיילים נטען מ-`?candidate_id=` (fallback: נועה לוי כברירת מחדל לדמו).

### Demo Flow (סיור מודרך)
`demo-guide.js` נטען בכל פורטל, פעיל **רק עם `?demo=1`**. פס הדרכה תחתון משרשר 6 שלבים (רישום → ELI5 → טכני → חינוך → חברות → סיום), נושא candidate_id, ומציג כפתור "⏩ דלג (דמו)" ב-ELI5/tech-test (`window.__demoSkip`) שמקפיץ ציון ריאליסטי בלי 15 דק' הקלדה. כניסה: כפתור "🎬 התחל סיור מודרך" ב-Hub.

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
├── maof-engine/                   # *** Backend חי *** — FastAPI + Supabase (Dual Scoring Engine)
│   ├── app.py · api/routes.py     # 30+ endpoints: score, match, eli5, 3 שכבות מבחן, CRUD, feedback
│   ├── scoring/                   # score_a.py · score_b.py · score_c.py · volume.py
│   ├── matching/hungarian.py      # שיבוץ אופטימלי
│   ├── nlp/                       # eli5 · code_test(שכבה2) · logic_test(שכבה1) · architecture_test(שכבה3) · systemic
│   ├── database/                  # Supabase client + repository (JSONB) + schema.sql
│   └── feedback/                  # Feedback Loop + weight store
├── maof-portals-deploy/           # פורטלים deployed ל-Vercel (HTML סטטי, ללא build)
│   ├── index.html                 # hub — ניווט + כפתור "🎬 התחל סיור מודרך"
│   ├── demo-guide.js              # Demo Flow — פס הדרכה חוצה-פורטלים (פעיל רק עם ?demo=1)
│   ├── soldiers/  companies/  education/
│   ├── eli5/index.html            # מבחן ELI5 (ציון A)
│   ├── tech-test/index.html       # מבחן טכני 3 שכבות (ציון B)
│   └── simulation/index.html      # סימולציית מודל 2+2
└── signal-news-demo/              # פרויקט נפרד — דמו מודיעין גיאופוליטי (Next.js)
```

### הפורטלים (maof-portals-deploy/)
| פורטל | משתמשים | פיצ'ר מרכזי |
|--------|---------|-------------|
| **soldiers/** | חיילים משוחררים | דשבורד אישי (טוען מ-candidate_id), רישום → DB, CTA למבחנים |
| **companies/** | חברות הייטק | מועמדים אמיתיים + score_b חי (/score/company), שיבוץ → Supabase |
| **education/** | משרד החינוך | מאגר מועמדים חי מה-API, ניהול צרכי STEM |
| **eli5/** | מועמדים | מבחן 5-שלבי (ציון A) — שומר ל-candidate, חזרה לפרופיל |
| **tech-test/** | מועמדים | מבחן טכני 3 שכבות (ציון B) — שומר logic/code/systemic/tech_test |
| **simulation/** | בעלי עניין | הדגמת מודל 2+2 + Hungarian |

> כל הפורטלים: HTML סטטי + CSS + Vanilla JS בלבד, RTL עברית, ללא build step. כולם מחוברים ל-`MAOF_API` (Render) ו-`demo-guide.js`.

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

- **Maof Portals Live:** https://maof-portals.vercel.app
- **Maof Engine API:** https://maof-project.onrender.com/api/v1 (FastAPI · `/health` · `/docs`)
- **Supabase:** Postgres (candidates/schools/companies/placements/eli5_results/feedback) — RLS מופעל, service_role רק ב-`.env` (gitignored)
- **GitHub:** https://github.com/Noam1316/maof-project (monorepo: engine + portals)
- **Signal News Live:** https://signal-news-demo.vercel.app/dashboard
- **Deploy commands:** portals → `cd maof-portals-deploy && npx vercel --prod --yes` · engine → git push (Render auto-deploy, ~90s)

---

## הערות לפיתוח

IMPORTANT: Rules for working in this codebase:
- Primary UI language: Hebrew (RTL).
- **The active system is מעוף**: `maof-engine/` (backend) + `maof-portals-deploy/` (frontend). `signal-news-demo/` is a separate side-project (see its own CLAUDE.md).
- **The Scoring Engine IS implemented** as a live FastAPI backend (`maof-engine/`) — see "מנוע מעוף — Backend חי" above. Not a spec anymore.
- **Groq is the LLM** (no Anthropic key) — 100K tokens/day free cap; when exhausted, grading silently falls back to heuristic (`method: "heuristic"`). The valid key is in Render env, NOT the local `.env` (which is expired).
- **Engine grading must always have a heuristic fallback** — never assume Groq is available.
- **Demo mode**: anything gated behind `?demo=1` (guide bar, skip buttons) must stay invisible in normal use.
- **candidate_id** flows via URL param + localStorage across all portals — preserve it when adding navigation.
- Portals: HTML + CSS + Vanilla JS, no build step. Mobile: keep `html{overflow-x:hidden}` + responsive grids — no horizontal scroll.
- Modify `maof-portals-deploy/` portals only on explicit request.
- Never commit `.env` (gitignored). Supabase service_role key bypasses RLS — never expose it.
- Deploy: portals via `npx vercel --prod --yes`; engine via git push (Render auto-deploy). Verify live after deploy.

### Signal News (side-project) rules
- Active Next.js project is `signal-news-demo/` — see its own CLAUDE.md.
- Signal vs Market is its priority feature. SectionNav has exactly 4 items. IntelHub uses tabs. `npm run build` MUST pass before push.
