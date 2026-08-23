from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from .db import connect, rows

# Metrics exclude UNVERIFIED/CONFLICTING_SOURCE and preserve stage separation by construction.
def analyse_topics(db: str, stage: str, include_partially_verified: bool = True) -> str:
    statuses = ("VERIFIED", "PARTIALLY_VERIFIED") if include_partially_verified else ("VERIFIED",)
    placeholders = ','.join('?' * len(statuses))
    params = (stage, *statuses)
    where = f"p.stage=? AND q.verification_status IN ({placeholders}) AND p.verification_status IN ({placeholders})"
    # Params appear twice in SQL conditions.
    params = (stage, *statuses, *statuses)
    with connect(db) as c:
        total_questions = c.execute(f"SELECT COUNT(*) FROM questions q JOIN papers p ON q.paper_id=p.paper_id WHERE {where}", params).fetchone()[0]
        total_papers = c.execute(f"SELECT COUNT(DISTINCT p.paper_id) FROM papers p JOIN questions q ON q.paper_id=p.paper_id WHERE {where}", params).fetchone()[0]
        run_id = "RUN-" + uuid.uuid4().hex[:12].upper()
        c.execute("INSERT INTO analysis_runs VALUES (?,?,?,?,?)",(run_id,datetime.now(timezone.utc).isoformat(timespec="seconds"),json.dumps({"stage":stage,"paper_status":statuses,"question_status":statuses}),"0.1.0",None))
        if not total_questions: return run_id
        sql = f"""SELECT q.section, COALESCE(q.topic, 'CLASSIFICATION_UNCERTAIN') topic,
                  COUNT(*) question_frequency, COUNT(DISTINCT p.paper_id) paper_frequency
                  FROM questions q JOIN papers p ON q.paper_id=p.paper_id WHERE {where}
                  GROUP BY q.section, COALESCE(q.topic, 'CLASSIFICATION_UNCERTAIN')"""
        for r in c.execute(sql,params):
            qf,pf=r["question_frequency"],r["paper_frequency"]
            coverage=100*pf/total_papers
            # Explicit mechanical rubric; users can revise it as corpus matures.
            priority = "P0" if coverage >= 80 and qf >= 10 else "P1" if coverage >= 60 else "P2" if coverage >= 35 else "P3" if coverage >= 15 else "P4"
            c.execute("""INSERT INTO topic_metrics VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
             (run_id,stage,r["section"],r["topic"],qf,pf,total_questions,total_papers,round(100*qf/total_questions,2),round(coverage,2),round(qf/total_papers,2),priority,"INSUFFICIENT_DATA"))
    return run_id

def report_markdown(db: str, stage: str, run_id: str | None = None) -> str:
    with connect(db) as c:
        if run_id is None:
            found=c.execute("SELECT run_id FROM analysis_runs WHERE json_extract(corpus_filter_json,'$.stage')=? ORDER BY created_at DESC LIMIT 1",(stage,)).fetchone()
            if not found: raise ValueError("No analysis run for stage. Run analyse first.")
            run_id=found[0]
        papers=rows(c,"SELECT year, exam_date, shift, paper_id, verification_status, total_questions FROM papers WHERE stage=? ORDER BY year, date_key, shift",(stage,))
        metrics=rows(c,"SELECT * FROM topic_metrics WHERE run_id=? ORDER BY question_frequency DESC, section, topic",(run_id,))
        sections=rows(c,"""SELECT q.section, COUNT(*) questions, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM questions q2 JOIN papers p2 ON p2.paper_id=q2.paper_id WHERE p2.stage=? AND q2.verification_status IN ('VERIFIED','PARTIALLY_VERIFIED') AND p2.verification_status IN ('VERIFIED','PARTIALLY_VERIFIED')),2) pct FROM questions q JOIN papers p ON p.paper_id=q.paper_id WHERE p.stage=? AND q.verification_status IN ('VERIFIED','PARTIALLY_VERIFIED') AND p.verification_status IN ('VERIFIED','PARTIALLY_VERIFIED') GROUP BY q.section ORDER BY questions DESC""",(stage,stage))
    out=[f"# SBI Clerk {stage.title()} — evidence-backed report", "", f"Analysis run: `{run_id}`", "", "## Corpus policy", "Only question and paper records marked VERIFIED or PARTIALLY_VERIFIED are counted. UNVERIFIED, CONFLICTING_SOURCE, and MISSING_SOURCE records are excluded. Prelims and Mains are never combined.", "", "## Paper inventory", "| Year | Date | Shift | Paper ID | Status | Declared questions |", "|---:|---|---|---|---|---:|"]
    out += [f"| {p['year']} | {p['exam_date'] or 'UNKNOWN'} | {p['shift']} | {p['paper_id']} | {p['verification_status']} | {p['total_questions'] if p['total_questions'] is not None else 'UNKNOWN'} |" for p in papers] or ["| — | — | — | No records | — | — |"]
    out += ["", "## Section distribution", "| Section | Questions | Question % |", "|---|---:|---:|"]
    out += [f"| {x['section']} | {x['questions']} | {x['pct']}% |" for x in sections] or ["| No verified question corpus yet | 0 | 0% |"]
    out += ["", "## Topic distribution", "Question % denominator: all analysed questions in this stage. Paper coverage denominator: distinct analysed papers in this stage.", "", "| Section | Topic | Q frequency | Paper frequency | Q % | Paper coverage | Avg Q/paper | Priority | Trend |", "|---|---|---:|---:|---:|---:|---:|---|---|"]
    out += [f"| {m['section']} | {m['topic']} | {m['question_frequency']} | {m['paper_frequency']} | {m['question_percentage']}% | {m['paper_coverage_percentage']}% | {m['average_questions_per_paper']} | {m['priority']} | {m['trend']} |" for m in metrics] or ["| No verified question corpus yet | — | 0 | 0 | 0% | 0% | 0 | UNRANKED | INSUFFICIENT_DATA |"]
    out += ["", "## Interpretation guardrail", "These are historical measurements, not a prediction or guarantee of future SBI Clerk questions. Trend and minimum-input recommendations require a sufficiently broad verified corpus; this report does not infer them from missing data."]
    return "\n".join(out)+"\n"
