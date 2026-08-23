# SBI Clerk real-paper collection corpus — Phase 1

This repository is currently **collection-only**: `COLLECT → VERIFY → SEPARATE → PRESERVE → VALIDATE`.

It contains no topic analysis, prediction, priority ranking, preparation plan, pattern model, or generated practice. It also does not claim that memory-based material is an official SBI paper.

## Corpus policy

- `papers/prelims/` and `papers/mains/` are separate. Every JSON file describes one paper/shift only; there is no annual merged-paper file.
- A source page describing a memory-based compilation is retained as **evidence of a secondary compilation**, not proof of an official released paper. The record is therefore normally `UNVERIFIED` + `PARTIAL` unless an independently inspectable complete source is stored.
- `MISSING_SOURCE` is an explicit research gap. It is not a paper and cannot contain questions.
- No question wording, answer, options, date, shift or section is inferred. `UNKNOWN` is preserved rather than guessed.
- `questions` are only added after their source document is inspected. Every question requires a source locator and preserves the source numbering. Unknown answer is stored literally as `UNKNOWN`.
- AI content has no importer or table in this Phase 1 repository.

## Layout

```text
papers/
  prelims/<year>/SBI_CLERK_PRELIMS_<year>_SHIFT_<n|UNKNOWN>.json
  mains/<year>/SBI_CLERK_MAINS_<year>_SHIFT_<n|UNKNOWN>.json
sources/source_registry.json
reports/PHASE_1_COLLECTION_REPORT.md
```

Each paper JSON contains provenance, completeness and verification status, evidence notes, and a `questions` array. An empty array means **no question text has been collected from the cited source**, not zero questions were asked.

## Status vocabulary

**Verification:** `VERIFIED`, `PARTIALLY_VERIFIED`, `UNVERIFIED`, `CONFLICTING_SOURCE`, `MISSING_SOURCE`.

**Completeness:** `COMPLETE`, `PARTIAL`, `UNVERIFIED`, `CONFLICTING_SOURCE`, `MISSING_SOURCE`.

## Database validation

The SQLite schema exists only to validate/import the raw collection; it performs no analysis.

```bash
python -m sbi_research.cli init --db data/sbi_clerk.sqlite
python -m sbi_research.cli import-sources sources/source_registry.json
find papers -name '*.json' -print0 | xargs -0 -n1 python -c 'import sys; from sbi_research.importer import import_papers; import_papers("data/sbi_clerk.sqlite", sys.argv[1])'
python -m sbi_research.cli validate --db data/sbi_clerk.sqlite
```

`paper_id`, stage, year, shift (or `UNKNOWN`), source, source URL, retrieval date, verification status, completeness status, and evidence note are mandatory for every non-missing record.
