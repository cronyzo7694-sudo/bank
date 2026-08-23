"""Import only explicit, provenance-bearing JSON records; no web scraping or reconstruction."""
from __future__ import annotations
import json
from pathlib import Path
from .constants import STAGES, VERIFICATION, SOURCE_TYPES, DIFFICULTIES, TIME_REQUIREMENTS
from .db import connect, json_value

class ImportErrorWithContext(ValueError): pass

def load_records(path: str | Path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload.get("records", [])

def _need(record, fields, label):
    missing = [field for field in fields if record.get(field) in (None, "")]
    if missing: raise ImportErrorWithContext(f"{label}: missing required field(s): {', '.join(missing)}")

def _choice(value, values, field):
    if value not in values: raise ImportErrorWithContext(f"invalid {field}={value!r}; expected one of {sorted(values)}")

def import_sources(db, path):
    records = load_records(path)
    with connect(db) as c:
      for r in records:
        _need(r, ["source_id","source_name","source_type","retrieval_date"], "source")
        _choice(r["source_type"], SOURCE_TYPES, "source_type")
        c.execute("""INSERT OR REPLACE INTO sources(source_id,source_name,source_url,source_type,retrieval_date,notes)
                     VALUES (:source_id,:source_name,:source_url,:source_type,:retrieval_date,:notes)""",
                  {**r, "source_url":r.get("source_url"), "notes":r.get("notes")})
    return len(records)

def import_papers(db, path):
    records = load_records(path)
    with connect(db) as c:
      for r in records:
        _need(r, ["paper_id","stage","year","verification_status"], "paper")
        _choice(r["stage"], STAGES, "stage"); _choice(r["verification_status"], VERIFICATION, "verification_status")
        date = r.get("exam_date")
        if date is not None and (len(date) != 10 or date[4] != '-' or date[7] != '-'):
            raise ImportErrorWithContext(f"paper {r['paper_id']}: exam_date must be ISO YYYY-MM-DD or null")
        if r["verification_status"] != "MISSING_SOURCE": _need(r, ["source_id"], f"paper {r['paper_id']}")
        values = {"paper_id":r["paper_id"], "exam_name":r.get("exam_name", "SBI Clerk"), "stage":r["stage"], "year":r["year"],
                  "exam_date":date, "date_key":date or "UNKNOWN", "shift":r.get("shift") or "UNKNOWN",
                  "total_questions":r.get("total_questions"), "sections_json":json_value(r.get("sections"), []),
                  "section_question_count_json":json_value(r.get("section_question_count"), {}), "source_id":r.get("source_id"),
                  "verification_status":r["verification_status"], "notes":r.get("notes")}
        c.execute("""INSERT OR REPLACE INTO papers VALUES
                   (:paper_id,:exam_name,:stage,:year,:exam_date,:date_key,:shift,:total_questions,:sections_json,:section_question_count_json,:source_id,:verification_status,:notes)""", values)
    return len(records)

def import_questions(db, path):
    records = load_records(path)
    with connect(db) as c:
      for r in records:
        _need(r, ["question_id","paper_id","section","question_number","question_text","verification_status"], "question")
        _choice(r["verification_status"], VERIFICATION - {"MISSING_SOURCE"}, "verification_status")
        _choice(r.get("difficulty", "UNCERTAIN"), DIFFICULTIES, "difficulty")
        _choice(r.get("time_requirement", "UNCERTAIN"), TIME_REQUIREMENTS, "time_requirement")
        paper = c.execute("SELECT source_id, verification_status FROM papers WHERE paper_id=?", (r["paper_id"],)).fetchone()
        if not paper: raise ImportErrorWithContext(f"question {r['question_id']}: unknown paper_id {r['paper_id']}")
        # A question's provenance may inherit its paper source, but source_locator remains required.
        source_id = r.get("source_id") or paper["source_id"]
        if not source_id: raise ImportErrorWithContext(f"question {r['question_id']}: no source_id or paper source")
        _need(r, ["source_locator"], f"question {r['question_id']}")
        values = {"question_id":r["question_id"], "paper_id":r["paper_id"], "section":r["section"], "question_number":str(r["question_number"]),
                  "question_text":r["question_text"], "options_json":json_value(r.get("options"), None), "correct_answer":r.get("correct_answer"),
                  "topic":r.get("topic"), "subtopic":r.get("subtopic"), "question_type":r.get("question_type"),
                  "difficulty":r.get("difficulty", "UNCERTAIN"), "time_requirement":r.get("time_requirement", "UNCERTAIN"),
                  "concept_tested":r.get("concept_tested"), "calculation_level":r.get("calculation_level"), "shortcut_available":r.get("shortcut_available"),
                  "common_trap":r.get("common_trap"), "recurrence_group":r.get("recurrence_group"), "pattern_id":r.get("pattern_id"),
                  "text_certainty":r.get("text_certainty", "CERTAIN"), "source_id":source_id, "source_locator":r["source_locator"],
                  "verification_status":r["verification_status"], "notes":r.get("notes")}
        c.execute("""INSERT OR REPLACE INTO questions VALUES
        (:question_id,:paper_id,:section,:question_number,:question_text,:options_json,:correct_answer,:topic,:subtopic,:question_type,:difficulty,:time_requirement,:concept_tested,:calculation_level,:shortcut_available,:common_trap,:recurrence_group,:pattern_id,:text_certainty,:source_id,:source_locator,:verification_status,:notes)""", values)
    return len(records)

def import_generated_practice(db, path):
    """Import AI-created exercises into their isolated table, never raw questions."""
    from datetime import datetime, timezone
    records = load_records(path)
    with connect(db) as c:
      for r in records:
        _need(r, ["practice_id", "stage", "section", "question_text", "generation_basis"], "AI-generated practice")
        _choice(r["stage"], STAGES, "stage")
        if r.get("source_type", "AI_GENERATED") != "AI_GENERATED":
            raise ImportErrorWithContext("generated practice must have source_type=AI_GENERATED")
        c.execute("""INSERT OR REPLACE INTO generated_practice VALUES
          (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", {
          "practice_id":r["practice_id"], "stage":r["stage"], "section":r["section"], "question_text":r["question_text"],
          "options_json":json_value(r.get("options"),None), "correct_answer":r.get("correct_answer"), "topic":r.get("topic"),
          "subtopic":r.get("subtopic"), "question_type":r.get("question_type"), "pattern_id":r.get("pattern_id"),
          "generation_basis":r["generation_basis"], "source_type":"AI_GENERATED",
          "created_at":r.get("created_at",datetime.now(timezone.utc).isoformat(timespec="seconds")), "notes":r.get("notes")})
    return len(records)
