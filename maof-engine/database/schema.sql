-- ============================================================
-- Maof Engine — Database Schema
-- PostgreSQL / Supabase
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Candidates ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS candidates (
    id                      TEXT PRIMARY KEY,
    name                    TEXT NOT NULL,
    email                   TEXT,
    eli5_score              FLOAT DEFAULT 0,
    subject                 TEXT NOT NULL,
    additional_subjects     TEXT[] DEFAULT '{}',
    distance_km             FLOAT DEFAULT 0,
    family_status_score     FLOAT DEFAULT 50,
    commitment_score        FLOAT DEFAULT 50,
    career_switches         INT DEFAULT 0,
    willing_periphery       BOOLEAN DEFAULT FALSE,
    tech_test_score         FLOAT DEFAULT 0,
    academic_background     TEXT DEFAULT 'regular_bagrut',
    independent_courses     INT DEFAULT 0,
    military_role           TEXT DEFAULT 'soldier',
    team_size               INT DEFAULT 1,
    conflict_resolution_score FLOAT DEFAULT 50,
    promotion_rate          FLOAT DEFAULT 50,
    preferred_company_size  TEXT DEFAULT 'medium',
    preferred_location      TEXT DEFAULT 'center',
    work_style              TEXT DEFAULT 'hybrid',
    willing_relocate        BOOLEAN DEFAULT FALSE,
    tech_stack              TEXT[] DEFAULT '{}',
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Schools ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS schools (
    id                      TEXT PRIMARY KEY,
    name                    TEXT NOT NULL,
    location                TEXT NOT NULL,
    lat                     FLOAT DEFAULT 31.5,
    lng                     FLOAT DEFAULT 34.8,
    required_subjects       TEXT[] DEFAULT '{}',
    grade_levels            TEXT[] DEFAULT '{}',
    socioeconomic_rank      INT DEFAULT 5,
    nurturing_index         INT DEFAULT 5,
    months_without_teacher  INT DEFAULT 0,
    budget_available        BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Companies ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS companies (
    id                      TEXT PRIMARY KEY,
    name                    TEXT NOT NULL,
    location                TEXT NOT NULL,
    lat                     FLOAT DEFAULT 32.08,
    lng                     FLOAT DEFAULT 34.78,
    size                    TEXT DEFAULT 'medium',
    work_style              TEXT DEFAULT 'hybrid',
    tech_stack              TEXT[] DEFAULT '{}',
    open_positions          INT DEFAULT 1,
    urgency_score           FLOAT DEFAULT 50,
    willing_station_b       BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Placements ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS placements (
    id                      TEXT PRIMARY KEY DEFAULT uuid_generate_v4()::TEXT,
    candidate_id            TEXT REFERENCES candidates(id),
    school_id               TEXT REFERENCES schools(id),
    company_id              TEXT REFERENCES companies(id),
    score_a                 FLOAT,
    score_b                 FLOAT,
    score_c                 FLOAT,
    volume_score            FLOAT,
    final_score             FLOAT,
    predicted_score         FLOAT,
    passes_threshold        BOOLEAN DEFAULT FALSE,
    rank                    INT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── School Feedback ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS school_feedback (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    placement_id            TEXT REFERENCES placements(id),
    candidate_id            TEXT REFERENCES candidates(id),
    school_id               TEXT REFERENCES schools(id),
    teacher_rating          FLOAT,
    attendance_rate         FLOAT,
    principal_satisfaction  FLOAT,
    student_satisfaction    FLOAT,
    actual_score            FLOAT,
    feedback_date           DATE DEFAULT CURRENT_DATE,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Company Feedback ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS company_feedback (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    placement_id            TEXT REFERENCES placements(id),
    candidate_id            TEXT REFERENCES candidates(id),
    company_id              TEXT REFERENCES companies(id),
    performance_score       FLOAT,
    progression_rate        FLOAT,
    manager_satisfaction    FLOAT,
    actual_score            FLOAT,
    feedback_date           DATE DEFAULT CURRENT_DATE,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Candidate Feedback ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS candidate_feedback (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    placement_id            TEXT REFERENCES placements(id),
    candidate_id            TEXT REFERENCES candidates(id),
    school_satisfaction     FLOAT,
    company_satisfaction    FLOAT,
    overall_satisfaction    FLOAT,
    actual_score            FLOAT,
    feedback_date           DATE DEFAULT CURRENT_DATE,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── ELI5 Test Results ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS eli5_results (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id            TEXT REFERENCES candidates(id),
    topic                   TEXT,
    text_score              FLOAT,
    chatbot_score           FLOAT,
    final_score             FLOAT,
    passes_minimum          BOOLEAN,
    breakdown               JSONB,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Code Test Results ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS code_test_results (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id            TEXT REFERENCES candidates(id),
    domain                  TEXT,
    final_level             INT,
    adaptive_score          FLOAT,
    passed                  BOOLEAN,
    results                 JSONB,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Indexes ────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_placements_candidate ON placements(candidate_id);
CREATE INDEX IF NOT EXISTS idx_placements_school ON placements(school_id);
CREATE INDEX IF NOT EXISTS idx_placements_company ON placements(company_id);
CREATE INDEX IF NOT EXISTS idx_placements_score ON placements(final_score DESC);
CREATE INDEX IF NOT EXISTS idx_school_feedback_placement ON school_feedback(placement_id);
CREATE INDEX IF NOT EXISTS idx_company_feedback_placement ON company_feedback(placement_id);

-- ─── Row Level Security (RLS) ───────────────────────────────
-- כל השירותים דרך ה-API עם service key — אין צורך ב-RLS כרגע
-- יופעל כשתתווסף auth לפורטלים

-- ─── Updated_at trigger ─────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER candidates_updated_at
    BEFORE UPDATE ON candidates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- Done. Run this in Supabase SQL Editor.
-- ============================================================
