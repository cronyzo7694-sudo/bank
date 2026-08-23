"""Phase 1 importer: only provenance-bearing paper metadata and source-preserved questions."""
from __future__ import annotations
import json
from pathlib import Path
from .constants import STAGES, VERIFICATION, COMPLETENESS, SOURCE_TYPES, TEXT_CERTAINTY
from .db import connect, json_value
class ImportErrorWithContext(ValueError): pass

def load_records(path):
 payload=json.loads(Path(path).read_text(encoding='utf-8')); return payload if isinstance(payload,list) else payload.get('records',[])
def _need(r,fs,label):
 m=[f for f in fs if r.get(f) in (None,'')]
 if m: raise ImportErrorWithContext(f"{label}: missing {', '.join(m)}")
def _choice(value, choices, name):
 if value not in choices: raise ImportErrorWithContext(f"invalid {name}: {value!r}")
def import_sources(db,path):
 records=load_records(path)
 with connect(db) as c:
  for r in records:
   _need(r,['source_id','source_name','source_url','source_type','retrieval_date'],'source'); _choice(r['source_type'],SOURCE_TYPES,'source_type')
   c.execute('INSERT OR REPLACE INTO sources VALUES (:source_id,:source_name,:source_url,:source_type,:retrieval_date,:notes)',{**r,'notes':r.get('notes')})
 return len(records)
def import_papers(db,path):
 records=load_records(path)
 with connect(db) as c:
  for r in records:
   _need(r,['paper_id','stage','year','verification_status','completeness_status','evidence_note'],'paper')
   _choice(r['stage'],STAGES,'stage'); _choice(r['verification_status'],VERIFICATION,'verification_status'); _choice(r['completeness_status'],COMPLETENESS,'completeness_status')
   if r['completeness_status']=='MISSING_SOURCE' and r.get('source_id'): raise ImportErrorWithContext(f"{r['paper_id']}: MISSING_SOURCE must not claim a source")
   if r['completeness_status']!='MISSING_SOURCE': _need(r,['source_id'],r['paper_id'])
   date=r.get('exam_date')
   v={'paper_id':r['paper_id'],'exam_name':r.get('exam_name','SBI Clerk'),'stage':r['stage'],'year':r['year'],'exam_date':date,'date_key':date or 'UNKNOWN','shift':r.get('shift') or 'UNKNOWN','total_questions':r.get('total_questions'),'sections_json':json_value(r.get('sections'),[]),'section_question_count_json':json_value(r.get('section_question_count'),{}),'source_id':r.get('source_id'),'verification_status':r['verification_status'],'completeness_status':r['completeness_status'],'evidence_note':r['evidence_note'],'notes':r.get('notes')}
   c.execute('INSERT OR REPLACE INTO papers VALUES (:paper_id,:exam_name,:stage,:year,:exam_date,:date_key,:shift,:total_questions,:sections_json,:section_question_count_json,:source_id,:verification_status,:completeness_status,:evidence_note,:notes)',v)
 return len(records)
def import_questions(db,path):
 records=load_records(path)
 with connect(db) as c:
  for r in records:
   _need(r,['question_id','paper_id','question_number','section','question_text','source_locator','verification_status'],'question')
   _choice(r['verification_status'],VERIFICATION-{'MISSING_SOURCE'},'verification_status'); _choice(r.get('text_certainty','CERTAIN'),TEXT_CERTAINTY,'text_certainty')
   paper=c.execute('SELECT source_id, completeness_status FROM papers WHERE paper_id=?',(r['paper_id'],)).fetchone()
   if not paper: raise ImportErrorWithContext(f"{r['question_id']}: unknown paper")
   if paper['completeness_status']=='MISSING_SOURCE': raise ImportErrorWithContext(f"{r['question_id']}: cannot add questions to MISSING_SOURCE")
   source_id=r.get('source_id') or paper['source_id']
   c.execute('INSERT OR REPLACE INTO questions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(r['question_id'],r['paper_id'],str(r['question_number']),r['section'],r['question_text'],json_value(r.get('options'),None),r.get('correct_answer','UNKNOWN'),source_id,r['source_locator'],r['verification_status'],r.get('text_certainty','CERTAIN'),r.get('notes')))
 return len(records)
