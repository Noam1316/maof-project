-- ══════════════════════════════════════════════════════════════
--  Maof Engine — Supabase Schema
--  הרץ ב-Supabase SQL Editor פעם אחת לפני הפעלת השרת
-- ══════════════════════════════════════════════════════════════

-- ─── Core entities (JSONB — flexible Pydantic models) ─────────

CREATE TABLE IF NOT EXISTS candidates (
  id          TEXT PRIMARY KEY,
  data        JSONB NOT NULL DEFAULT '{}',
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS schools (
  id          TEXT PRIMARY KEY,
  data        JSONB NOT NULL DEFAULT '{}',
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS companies (
  id          TEXT PRIMARY KEY,
  data        JSONB NOT NULL DEFAULT '{}',
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Placements (Hungarian output) ───────────────────────────

CREATE TABLE IF NOT EXISTS placements (
  id              TEXT PRIMARY KEY,
  candidate_id    TEXT NOT NULL,
  school_id       TEXT NOT NULL,
  company_id      TEXT NOT NULL,
  score_a         FLOAT,
  score_b         FLOAT,
  score_c         FLOAT,
  volume_score    FLOAT,
  final_score     FLOAT NOT NULL DEFAULT 0,
  placement_date  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Assessment results ────────────────────────────────────────

CREATE TABLE IF NOT EXISTS eli5_results (
  id               BIGSERIAL PRIMARY KEY,
  candidate_id     TEXT NOT NULL,
  topic            TEXT NOT NULL DEFAULT 'general',
  text_score       FLOAT,
  chatbot_score    FLOAT,
  final_score      FLOAT,
  passes_minimum   BOOL DEFAULT FALSE,
  breakdown        JSONB DEFAULT '{}',
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS code_test_results (
  id               BIGSERIAL PRIMARY KEY,
  candidate_id     TEXT NOT NULL,
  domain           TEXT,
  final_level      INT DEFAULT 0,
  adaptive_score   FLOAT DEFAULT 0,
  passed           BOOL DEFAULT FALSE,
  results          JSONB DEFAULT '[]',
  created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Feedback Loop ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS school_feedback (
  id                     BIGSERIAL PRIMARY KEY,
  placement_id           TEXT NOT NULL,
  candidate_id           TEXT NOT NULL,
  school_id              TEXT NOT NULL,
  teacher_rating         FLOAT,
  attendance_rate        FLOAT,
  principal_satisfaction FLOAT,
  student_satisfaction   FLOAT,
  actual_score           FLOAT,
  date                   TEXT,
  created_at             TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS company_feedback (
  id                   BIGSERIAL PRIMARY KEY,
  placement_id         TEXT NOT NULL,
  candidate_id         TEXT NOT NULL,
  company_id           TEXT NOT NULL,
  performance_score    FLOAT,
  progression_rate     FLOAT,
  manager_satisfaction FLOAT,
  actual_score         FLOAT,
  date                 TEXT,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS candidate_feedback (
  id                   BIGSERIAL PRIMARY KEY,
  placement_id         TEXT NOT NULL,
  candidate_id         TEXT NOT NULL,
  school_satisfaction  FLOAT,
  company_satisfaction FLOAT,
  overall_satisfaction FLOAT,
  actual_score         FLOAT,
  date                 TEXT,
  created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Indexes ──────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_placements_candidate  ON placements(candidate_id);
CREATE INDEX IF NOT EXISTS idx_eli5_candidate        ON eli5_results(candidate_id);
CREATE INDEX IF NOT EXISTS idx_code_candidate        ON code_test_results(candidate_id);
CREATE INDEX IF NOT EXISTS idx_sfb_placement         ON school_feedback(placement_id);
CREATE INDEX IF NOT EXISTS idx_cfb_placement         ON company_feedback(placement_id);
CREATE INDEX IF NOT EXISTS idx_candfb_placement      ON candidate_feedback(placement_id);

-- ─── RLS: allow service role full access ──────────────────────

ALTER TABLE candidates         ENABLE ROW LEVEL SECURITY;
ALTER TABLE schools            ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies          ENABLE ROW LEVEL SECURITY;
ALTER TABLE placements         ENABLE ROW LEVEL SECURITY;
ALTER TABLE eli5_results       ENABLE ROW LEVEL SECURITY;
ALTER TABLE code_test_results  ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_feedback    ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_feedback   ENABLE ROW LEVEL SECURITY;
ALTER TABLE candidate_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_full" ON candidates         FOR ALL USING (true);
CREATE POLICY "service_full" ON schools            FOR ALL USING (true);
CREATE POLICY "service_full" ON companies          FOR ALL USING (true);
CREATE POLICY "service_full" ON placements         FOR ALL USING (true);
CREATE POLICY "service_full" ON eli5_results       FOR ALL USING (true);
CREATE POLICY "service_full" ON code_test_results  FOR ALL USING (true);
CREATE POLICY "service_full" ON school_feedback    FOR ALL USING (true);
CREATE POLICY "service_full" ON company_feedback   FOR ALL USING (true);
CREATE POLICY "service_full" ON candidate_feedback FOR ALL USING (true);
