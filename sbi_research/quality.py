from __future__ import annotations
from datetime import datetime, timezone
from .db import connect

def validate(db: str) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    issues = []
    def add(severity, typ, ident, code, message):
        issues.append({"severity":severity,"entity_type":typ,"entity_id":str(ident),"code":code,"message":message})
    with connect(db) as c:
        c.execute("DELETE FROM validation_issues")
        papers = c.execute("SELECT * FROM papers").fetchall()
        for p in papers:
            actual = c.execute("SELECT COUNT(*) FROM questions WHERE paper_id=?", (p["paper_id"],)).fetchone()[0]
            if p["verification_status"] == "MISSING_SOURCE" and actual:
                add("ERROR","paper",p["paper_id"],"QUESTIONS_ON_MISSING_SOURCE","MISSING_SOURCE papers cannot contain question records.")
            if p["total_questions"] is not None and actual and actual != p["total_questions"]:
                add("WARNING","paper",p["paper_id"],"TOTAL_MISMATCH",f"metadata total_questions={p['total_questions']}; imported questions={actual}.")
            if p["verification_status"] != "MISSING_SOURCE" and not p["source_id"]:
                add("ERROR","paper",p["paper_id"],"MISSING_PROVENANCE","Paper has no source.")
            # Section totals are checked only once any questions are present.
            import json
            stated = json.loads(p["section_question_count_json"])
            if actual and stated:
                for section, expected in stated.items():
                    got = c.execute("SELECT COUNT(*) FROM questions WHERE paper_id=? AND section=?",(p["paper_id"],section)).fetchone()[0]
                    if got != expected: add("WARNING","paper",p["paper_id"],"SECTION_TOTAL_MISMATCH",f"{section}: metadata={expected}; imported={got}.")
        qrows = c.execute("""SELECT q.*, s.source_type FROM questions q LEFT JOIN sources s ON s.source_id=q.source_id""").fetchall()
        for q in qrows:
            for field in ("topic","subtopic","question_type"):
                if not q[field]: add("WARNING","question",q["question_id"],"MISSING_CLASSIFICATION",f"{field} is not assigned.")
            if not q["source_id"] or not q["source_locator"]: add("ERROR","question",q["question_id"],"MISSING_PROVENANCE","Question needs source and source_locator.")
            if q["source_type"] == "AI_GENERATED": add("ERROR","question",q["question_id"],"GENERATED_IN_RAW","AI-generated source linked into REAL raw questions.")
            if q["text_certainty"] == "TEXT_UNCERTAIN": add("WARNING","question",q["question_id"],"TEXT_UNCERTAIN","Do not quote as exact wording.")
        for i in issues:
            c.execute("INSERT INTO validation_issues(run_at,severity,entity_type,entity_id,code,message) VALUES (?,?,?,?,?,?)",
                      (now, i["severity"], i["entity_type"], i["entity_id"], i["code"], i["message"]))
    return issues
