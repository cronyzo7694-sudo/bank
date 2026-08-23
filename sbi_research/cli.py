from __future__ import annotations
import argparse
from pathlib import Path
from .db import initialise
from .importer import import_sources, import_papers, import_questions, import_generated_practice
from .quality import validate
from .analysis import analyse_topics, report_markdown

def main(argv=None):
    parser=argparse.ArgumentParser(prog="sbi-research", description="Evidence-first SBI Clerk research database")
    sub=parser.add_subparsers(dest="command",required=True)
    init=sub.add_parser("init"); init.add_argument("--db",default="data/sbi_clerk.sqlite")
    for name in ("sources","papers","questions","generated-practice"):
        p=sub.add_parser("import-"+name); p.add_argument("file"); p.add_argument("--db",default="data/sbi_clerk.sqlite")
    p=sub.add_parser("validate"); p.add_argument("--db",default="data/sbi_clerk.sqlite")
    p=sub.add_parser("analyse"); p.add_argument("--stage",choices=["PRELIMS","MAINS"],required=True); p.add_argument("--db",default="data/sbi_clerk.sqlite"); p.add_argument("--verified-only",action="store_true")
    p=sub.add_parser("report"); p.add_argument("--stage",choices=["PRELIMS","MAINS"],required=True); p.add_argument("--run-id"); p.add_argument("--out",required=True); p.add_argument("--db",default="data/sbi_clerk.sqlite")
    args=parser.parse_args(argv)
    if args.command=="init": initialise(args.db); print(f"Initialized {args.db}")
    elif args.command.startswith("import-"):
        initialise(args.db); fn={"import-sources":import_sources,"import-papers":import_papers,"import-questions":import_questions,"import-generated-practice":import_generated_practice}[args.command]
        print(f"Imported {fn(args.db,args.file)} {args.command.removeprefix('import-')} record(s).")
    elif args.command=="validate":
        issues=validate(args.db)
        for x in issues: print(f"{x['severity']} {x['entity_type']}:{x['entity_id']} {x['code']} — {x['message']}")
        print(f"Validation complete: {len(issues)} issue(s).")
        if any(x['severity']=="ERROR" for x in issues): return 2
    elif args.command=="analyse": print(analyse_topics(args.db,args.stage,not args.verified_only))
    elif args.command=="report":
        Path(args.out).parent.mkdir(parents=True,exist_ok=True); Path(args.out).write_text(report_markdown(args.db,args.stage,args.run_id),encoding="utf-8"); print(f"Wrote {args.out}")
if __name__=="__main__": main()
