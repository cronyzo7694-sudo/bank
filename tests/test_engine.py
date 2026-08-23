import json
from pathlib import Path
from sbi_research.db import initialise, connect
from sbi_research.importer import import_sources, import_papers, import_questions
from sbi_research.analysis import analyse_topics
from sbi_research.quality import validate

def write(path, records):
    path.write_text(json.dumps({"records":records}), encoding="utf8")

def test_stage_isolated_metrics(tmp_path):
    db=tmp_path/'x.sqlite'; initialise(db)
    sources=tmp_path/'s.json'; papers=tmp_path/'p.json'; qs=tmp_path/'q.json'
    write(sources,[{"source_id":"TEST","source_name":"test fixture","source_url":"https://example.test","source_type":"USER_PROVIDED","retrieval_date":"2026-08-23"}])
    write(papers,[
      {"paper_id":"P","stage":"PRELIMS","year":2024,"exam_date":"2024-01-01","shift":"Shift 1","total_questions":1,"source_id":"TEST","verification_status":"VERIFIED"},
      {"paper_id":"M","stage":"MAINS","year":2024,"exam_date":"2024-01-01","shift":"Shift 1","total_questions":1,"source_id":"TEST","verification_status":"VERIFIED"}])
    write(qs,[
      {"question_id":"P1","paper_id":"P","section":"Numerical Ability","question_number":"Q1","question_text":"fixture","topic":"Percentage","subtopic":"Basic","question_type":"Direct Calculation","difficulty":"EASY","time_requirement":"FAST","source_locator":"p1","verification_status":"VERIFIED"},
      {"question_id":"M1","paper_id":"M","section":"General English","question_number":"Q1","question_text":"fixture","topic":"Vocabulary","subtopic":"Word","question_type":"Vocabulary","difficulty":"EASY","time_requirement":"FAST","source_locator":"p1","verification_status":"VERIFIED"}])
    import_sources(db,sources); import_papers(db,papers); import_questions(db,qs)
    run=analyse_topics(db,"PRELIMS")
    with connect(db) as c:
      metric=c.execute("SELECT topic,total_questions FROM topic_metrics WHERE run_id=?",(run,)).fetchone()
    assert tuple(metric)==("Percentage",1)
    assert not [x for x in validate(db) if x['severity']=='ERROR']
