from datetime import datetime, timezone
from .db import connect

def validate(db):
 issues=[]; now=datetime.now(timezone.utc).isoformat(timespec='seconds')
 def add(sev,t,i,code,msg): issues.append(dict(severity=sev,entity_type=t,entity_id=str(i),code=code,message=msg))
 with connect(db) as c:
  c.execute('DELETE FROM validation_issues')
  for p in c.execute('SELECT * FROM papers'):
   count=c.execute('SELECT COUNT(*) FROM questions WHERE paper_id=?',(p['paper_id'],)).fetchone()[0]
   if p['completeness_status']=='MISSING_SOURCE' and count: add('ERROR','paper',p['paper_id'],'QUESTIONS_ON_MISSING_SOURCE','Missing-source entry cannot contain questions.')
   if p['completeness_status']!='MISSING_SOURCE' and not p['source_id']: add('ERROR','paper',p['paper_id'],'MISSING_PROVENANCE','Paper needs source_id.')
   if p['total_questions'] is not None and count and count != p['total_questions']: add('WARNING','paper',p['paper_id'],'TOTAL_MISMATCH',f"Declared {p['total_questions']}, stored {count}.")
   if p['completeness_status']=='COMPLETE' and not count: add('ERROR','paper',p['paper_id'],'EMPTY_COMPLETE','COMPLETE paper has no questions.')
   if p['paper_access_status']=='PAPER_FOUND' and not count: add('ERROR','paper',p['paper_id'],'UNEXTRACTED_FOUND_PAPER','PAPER_FOUND requires at least one directly extracted question.')
  for q in c.execute('SELECT q.*,p.completeness_status FROM questions q JOIN papers p ON p.paper_id=q.paper_id'):
   if not q['source_id']: add('ERROR','question',q['question_id'],'MISSING_PROVENANCE','Question has no resolvable source.')
   if q['correct_answer'] != 'UNKNOWN' and (not q['answer_source_id'] or not q['answer_source_url']): add('ERROR','question',q['question_id'],'UNSUPPORTED_ANSWER','Non-UNKNOWN answer requires answer-source provenance.')
   if q['text_certainty']=='TEXT_UNCERTAIN': add('WARNING','question',q['question_id'],'TEXT_UNCERTAIN','Do not quote as exact wording.')
  for x in issues: c.execute('INSERT INTO validation_issues(run_at,severity,entity_type,entity_id,code,message) VALUES (?,?,?,?,?,?)',(now,x['severity'],x['entity_type'],x['entity_id'],x['code'],x['message']))
 return issues
