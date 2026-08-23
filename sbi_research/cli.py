from __future__ import annotations
import argparse
from .db import initialise
from .importer import import_sources, import_papers, import_questions
from .quality import validate

def main(argv=None):
 p=argparse.ArgumentParser(prog='sbi-research',description='SBI Clerk Phase 1: collect, preserve, validate')
 sub=p.add_subparsers(dest='command',required=True)
 x=sub.add_parser('init'); x.add_argument('--db',default='data/sbi_clerk.sqlite')
 for name in ('sources','papers','questions'):
  x=sub.add_parser('import-'+name); x.add_argument('file'); x.add_argument('--db',default='data/sbi_clerk.sqlite')
 x=sub.add_parser('validate'); x.add_argument('--db',default='data/sbi_clerk.sqlite')
 a=p.parse_args(argv)
 if a.command=='init': initialise(a.db); print(f'Initialized {a.db}')
 elif a.command.startswith('import-'):
  initialise(a.db); f={'import-sources':import_sources,'import-papers':import_papers,'import-questions':import_questions}[a.command]; print(f'Imported {f(a.db,a.file)} record(s).')
 else:
  issues=validate(a.db)
  for i in issues: print(f"{i['severity']} {i['entity_type']}:{i['entity_id']} {i['code']} — {i['message']}")
  print(f'Validation complete: {len(issues)} issue(s).')
  if any(i['severity']=='ERROR' for i in issues): return 2
if __name__=='__main__': main()
