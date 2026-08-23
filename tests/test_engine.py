import json, tempfile
from pathlib import Path
from sbi_research.db import initialise, connect
from sbi_research.importer import import_sources, import_papers, import_questions, ImportErrorWithContext
from sbi_research.quality import validate

def put(path, records): path.write_text(json.dumps({'records':records}))
def test_missing_source_cannot_receive_questions():
 with tempfile.TemporaryDirectory() as td:
  d=Path(td); db=d/'x.sqlite'; initialise(db)
  p=d/'p.json'; q=d/'q.json'
  put(p,[{'paper_id':'SBI_CLERK_PRELIMS_2017_SHIFT_UNKNOWN','stage':'PRELIMS','year':2017,'verification_status':'MISSING_SOURCE','completeness_status':'MISSING_SOURCE','evidence_note':'No source found.'}])
  put(q,[{'question_id':'x','paper_id':'SBI_CLERK_PRELIMS_2017_SHIFT_UNKNOWN','question_number':'1','section':'UNKNOWN','question_text':'Never import','source_locator':'x','verification_status':'UNVERIFIED'}])
  import_papers(db,p)
  try: import_questions(db,q); assert False
  except ImportErrorWithContext: pass
  assert not [x for x in validate(db) if x['severity']=='ERROR']
