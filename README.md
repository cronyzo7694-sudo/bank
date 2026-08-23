# SBI Clerk Master Research Engine

An **evidence-first local database** for SBI Clerk paper research. It is intentionally empty of purported PYQs: this repository will not turn remembered, reconstructed, or scraped-without-provenance questions into “real papers.”

## Non-negotiable data contract

- `PRELIMS` and `MAINS` are separate values at the paper, question, and analysis level. No command aggregates them.
- Each paper is uniquely identified by `stage + year + date_key + shift`; unknown date/shift are stored as `UNKNOWN`, never guessed.
- Raw (`papers`, `questions`) and derived (`analysis_runs`, `topic_metrics`) data are separate tables.
- A question keeps its source question number verbatim (`question_number` is text).
- Question records require a source locator (page, question URL, PDF page, or equivalent). A paper source may be inherited, but cannot be absent.
- `MISSING_SOURCE` inventory records may not contain questions.
- Analysis excludes `UNVERIFIED`, `CONFLICTING_SOURCE`, and `MISSING_SOURCE` material. It labels metrics as historical, never predictive guarantees.
- AI exercises belong only in the `generated_practice` table and are always `AI_GENERATED`; they cannot be imported into `questions`.

## Quick start

```bash
python -m sbi_research.cli init --db data/sbi_clerk.sqlite
python -m sbi_research.cli import-papers data/raw/paper_inventory.json --db data/sbi_clerk.sqlite
python -m sbi_research.cli validate --db data/sbi_clerk.sqlite
python -m sbi_research.cli analyse --stage PRELIMS --db data/sbi_clerk.sqlite
python -m sbi_research.cli report --stage PRELIMS --out docs/prelims_report.md --db data/sbi_clerk.sqlite
```

The included inventory contains only a clearly marked source gap. It is **not** a question paper and has no question records.

## Import order

1. `init`
2. `import-sources` — source registry
3. `import-papers` — one independently identifiable paper/shift per record
4. `import-questions` — source-preserved questions
5. `validate` — resolve errors before publishing analysis
6. `analyse` separately for `PRELIMS` and `MAINS`
7. `report`

The input files are JSON objects with a `records` array (a top-level JSON array also works).

### Source record

```json
{
  "source_id": "SRC-EXAMPLE",
  "source_name": "Publisher / archive name",
  "source_url": "https://example.org/paper",
  "source_type": "SECONDARY_SOURCE",
  "retrieval_date": "2026-08-23",
  "notes": "State whether it is an official document or a secondary reproduction."
}
```

Allowed `source_type`: `OFFICIAL`, `SECONDARY_SOURCE`, `QUESTION_ARCHIVE`, `USER_PROVIDED`, `AI_GENERATED`, `UNVERIFIED`.

### Paper record

```json
{
  "paper_id": "SBI_CLERK_PRELIMS_2024_2024-01-05_SHIFT_1",
  "exam_name": "SBI Clerk",
  "stage": "PRELIMS",
  "year": 2024,
  "exam_date": "2024-01-05",
  "shift": "Shift 1",
  "total_questions": 100,
  "sections": ["English Language", "Numerical Ability", "Reasoning Ability"],
  "section_question_count": {"English Language": 30, "Numerical Ability": 35, "Reasoning Ability": 35},
  "source_id": "SRC-EXAMPLE",
  "verification_status": "PARTIALLY_VERIFIED",
  "notes": "Use null/UNKNOWN rather than assumptions."
}
```

This is a **schema example only**, not a claim about an actual paper, date, or distribution.

### Question record

```json
{
  "question_id": "SBI_CLERK_PRELIMS_2024_2024-01-05_SHIFT_1_Q37",
  "paper_id": "SBI_CLERK_PRELIMS_2024_2024-01-05_SHIFT_1",
  "section": "Numerical Ability",
  "question_number": "Q37",
  "question_text": "Exact source wording goes here; do not paraphrase.",
  "options": ["…", "…", "…", "…", "…"],
  "correct_answer": "B",
  "topic": "Percentage",
  "subtopic": "Successive Percentage",
  "question_type": "Word Problem",
  "difficulty": "MODERATE",
  "time_requirement": "MODERATE",
  "pattern_id": "PATTERN-ARITH-001",
  "source_locator": "PDF page 7, Q37",
  "verification_status": "PARTIALLY_VERIFIED"
}
```

`source_id` is optional in the question file only when it intentionally inherits the paper source. `source_locator` is always mandatory. `TEXT_UNCERTAIN` can be used for `text_certainty`; do not quote such wording as exact.

## Verification and quality gates

`validate` checks provenance, forbidden generated material in the raw corpus, question-count and section-count mismatches, and incomplete classification. Warnings should be resolved or documented before using reports; errors block a clean research release.

Topic metrics expose both **question frequency** and **paper frequency**, plus separate question percentage and paper coverage. The current priority rubric is mechanical and visible in `sbi_research/analysis.py`; it should only be treated as a preparation aid after enough verified papers exist. Trends deliberately remain `INSUFFICIENT_DATA` until a dedicated year-wise trend model is supplied with a broad corpus.

## Data handling

Do not add copyrighted bulk paper text without a legitimate source/right to retain it. Keep source URLs, retrieval dates, source type, and locators. Preserve conflicts instead of choosing a version silently. Do not use this engine to make future-exam guarantees.
