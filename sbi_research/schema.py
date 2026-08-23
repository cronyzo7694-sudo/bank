SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
  source_id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_url TEXT,
  source_type TEXT NOT NULL,
  retrieval_date TEXT NOT NULL,
  notes TEXT,
  CHECK(source_type IN ('OFFICIAL','SECONDARY_SOURCE','QUESTION_ARCHIVE','USER_PROVIDED','AI_GENERATED','UNVERIFIED'))
);

-- RAW layer: a row is one paper/shift, never a year-level amalgam.
CREATE TABLE IF NOT EXISTS papers (
  paper_id TEXT PRIMARY KEY,
  exam_name TEXT NOT NULL DEFAULT 'SBI Clerk',
  stage TEXT NOT NULL CHECK(stage IN ('PRELIMS','MAINS')),
  year INTEGER NOT NULL CHECK(year BETWEEN 1990 AND 2100),
  exam_date TEXT, -- ISO date only; NULL means unknown, not guessed
  date_key TEXT NOT NULL, -- date or UNKNOWN, required for shift-safe identity
  shift TEXT NOT NULL DEFAULT 'UNKNOWN',
  total_questions INTEGER,
  sections_json TEXT NOT NULL DEFAULT '[]',
  section_question_count_json TEXT NOT NULL DEFAULT '{}',
  source_id TEXT,
  verification_status TEXT NOT NULL,
  notes TEXT,
  UNIQUE(stage, year, date_key, shift),
  FOREIGN KEY(source_id) REFERENCES sources(source_id),
  CHECK(verification_status IN ('VERIFIED','PARTIALLY_VERIFIED','UNVERIFIED','CONFLICTING_SOURCE','MISSING_SOURCE')),
  CHECK((verification_status = 'MISSING_SOURCE' AND source_id IS NULL) OR verification_status != 'MISSING_SOURCE')
);

-- RAW layer only. Original wording is never replaced with classifications.
CREATE TABLE IF NOT EXISTS questions (
  question_id TEXT PRIMARY KEY,
  paper_id TEXT NOT NULL,
  section TEXT NOT NULL,
  question_number TEXT NOT NULL, -- text preserves source labels such as Q37 / 37(a)
  question_text TEXT NOT NULL,
  options_json TEXT,
  correct_answer TEXT,
  topic TEXT,
  subtopic TEXT,
  question_type TEXT,
  difficulty TEXT NOT NULL DEFAULT 'UNCERTAIN',
  time_requirement TEXT NOT NULL DEFAULT 'UNCERTAIN',
  concept_tested TEXT,
  calculation_level TEXT,
  shortcut_available TEXT,
  common_trap TEXT,
  recurrence_group TEXT,
  pattern_id TEXT,
  text_certainty TEXT NOT NULL DEFAULT 'CERTAIN',
  source_id TEXT,
  source_locator TEXT,
  verification_status TEXT NOT NULL,
  notes TEXT,
  FOREIGN KEY(paper_id) REFERENCES papers(paper_id) ON DELETE RESTRICT,
  FOREIGN KEY(source_id) REFERENCES sources(source_id),
  UNIQUE(paper_id, question_number),
  CHECK(difficulty IN ('EASY','MODERATE','HARD','UNCERTAIN')),
  CHECK(time_requirement IN ('VERY_FAST','FAST','MODERATE','TIME_CONSUMING','UNCERTAIN')),
  CHECK(text_certainty IN ('CERTAIN','TEXT_UNCERTAIN')),
  CHECK(verification_status IN ('VERIFIED','PARTIALLY_VERIFIED','UNVERIFIED','CONFLICTING_SOURCE'))
);

-- Separate derivative layer. It never mutates questions/papers.
CREATE TABLE IF NOT EXISTS analysis_runs (
  run_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  corpus_filter_json TEXT NOT NULL,
  engine_version TEXT NOT NULL,
  notes TEXT
);
CREATE TABLE IF NOT EXISTS topic_metrics (
  run_id TEXT NOT NULL,
  stage TEXT NOT NULL,
  section TEXT NOT NULL,
  topic TEXT NOT NULL,
  question_frequency INTEGER NOT NULL,
  paper_frequency INTEGER NOT NULL,
  total_questions INTEGER NOT NULL,
  total_papers INTEGER NOT NULL,
  question_percentage REAL NOT NULL,
  paper_coverage_percentage REAL NOT NULL,
  average_questions_per_paper REAL NOT NULL,
  priority TEXT NOT NULL DEFAULT 'UNRANKED',
  trend TEXT NOT NULL DEFAULT 'INSUFFICIENT_DATA',
  PRIMARY KEY(run_id, stage, section, topic),
  FOREIGN KEY(run_id) REFERENCES analysis_runs(run_id),
  CHECK(priority IN ('P0','P1','P2','P3','P4','UNRANKED')),
  CHECK(trend IN ('INCREASING','STABLE','DECREASING','EMERGING','INSUFFICIENT_DATA'))
);
CREATE TABLE IF NOT EXISTS validation_issues (
  issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_at TEXT NOT NULL,
  severity TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  code TEXT NOT NULL,
  message TEXT NOT NULL
);

-- Generated exercises are physically separate from the real-paper corpus.
CREATE TABLE IF NOT EXISTS generated_practice (
  practice_id TEXT PRIMARY KEY,
  stage TEXT NOT NULL CHECK(stage IN ('PRELIMS','MAINS')),
  section TEXT NOT NULL,
  question_text TEXT NOT NULL,
  options_json TEXT,
  correct_answer TEXT,
  topic TEXT,
  subtopic TEXT,
  question_type TEXT,
  pattern_id TEXT,
  generation_basis TEXT NOT NULL,
  source_type TEXT NOT NULL DEFAULT 'AI_GENERATED' CHECK(source_type = 'AI_GENERATED'),
  created_at TEXT NOT NULL,
  notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_questions_paper ON questions(paper_id);
CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(section, topic);
CREATE INDEX IF NOT EXISTS idx_papers_stage_year ON papers(stage, year);
"""
