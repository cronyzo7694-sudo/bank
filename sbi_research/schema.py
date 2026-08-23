SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS sources (
 source_id TEXT PRIMARY KEY, source_name TEXT NOT NULL, source_url TEXT NOT NULL,
 source_type TEXT NOT NULL CHECK(source_type IN ('OFFICIAL','REPUTABLE_EDUCATIONAL','QUESTION_ARCHIVE','USER_PROVIDED','OTHER')),
 retrieval_date TEXT NOT NULL, notes TEXT
);
-- RAW COLLECTION LAYER ONLY. One row = one separately identifiable paper/shift.
CREATE TABLE IF NOT EXISTS papers (
 paper_id TEXT PRIMARY KEY, exam_name TEXT NOT NULL DEFAULT 'SBI Clerk',
 stage TEXT NOT NULL CHECK(stage IN ('PRELIMS','MAINS','UNKNOWN_STAGE')),
 year INTEGER NOT NULL CHECK(year BETWEEN 1990 AND 2100), exam_date TEXT,
 date_key TEXT NOT NULL, shift TEXT NOT NULL DEFAULT 'UNKNOWN',
 total_questions INTEGER, sections_json TEXT NOT NULL DEFAULT '[]',
 section_question_count_json TEXT NOT NULL DEFAULT '{}', source_id TEXT,
 verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED','PARTIALLY_VERIFIED','UNVERIFIED','CONFLICTING_SOURCE','MISSING_SOURCE')),
 paper_access_status TEXT NOT NULL DEFAULT 'SOURCE_LEAD' CHECK(paper_access_status IN ('SOURCE_LEAD','PAPER_FOUND','VERIFIED')),
 completeness_status TEXT NOT NULL CHECK(completeness_status IN ('COMPLETE','PARTIAL','MISSING_SOURCE','UNVERIFIED','CONFLICTING_SOURCE')),
 evidence_note TEXT NOT NULL, notes TEXT,
 UNIQUE(stage,year,date_key,shift), FOREIGN KEY(source_id) REFERENCES sources(source_id),
 CHECK((completeness_status='MISSING_SOURCE' AND source_id IS NULL) OR completeness_status!='MISSING_SOURCE')
);
-- Questions are source-preserved only. No topic, pattern, priority, or generated fields in Phase 1.
CREATE TABLE IF NOT EXISTS questions (
 question_id TEXT PRIMARY KEY, paper_id TEXT NOT NULL, question_number TEXT NOT NULL,
 section TEXT NOT NULL, question_text TEXT NOT NULL, options_json TEXT, correct_answer TEXT NOT NULL DEFAULT 'UNKNOWN',
 source_id TEXT, source_locator TEXT NOT NULL, verification_status TEXT NOT NULL CHECK(verification_status IN ('VERIFIED','PARTIALLY_VERIFIED','UNVERIFIED','CONFLICTING_SOURCE')),
 text_certainty TEXT NOT NULL DEFAULT 'CERTAIN' CHECK(text_certainty IN ('CERTAIN','TEXT_UNCERTAIN')),
 notes TEXT, FOREIGN KEY(paper_id) REFERENCES papers(paper_id), FOREIGN KEY(source_id) REFERENCES sources(source_id),
 UNIQUE(paper_id,question_number)
);
CREATE TABLE IF NOT EXISTS validation_issues (
 issue_id INTEGER PRIMARY KEY AUTOINCREMENT, run_at TEXT NOT NULL, severity TEXT NOT NULL,
 entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, code TEXT NOT NULL, message TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_questions_paper ON questions(paper_id);
CREATE INDEX IF NOT EXISTS idx_papers_stage_year ON papers(stage,year);
"""
