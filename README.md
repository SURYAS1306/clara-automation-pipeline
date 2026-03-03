## Clara Automation Pipeline

This repository implements a **zero-cost, deterministic Clara Answers automation pipeline** that converts demo and onboarding call transcripts into:

- **Versioned account memos** (`memo.json`)
- **Retell Agent Specs** (`agent_spec.json`)
- **Per-account changelogs** (field-level diffs)
- **Per-account logs** (extraction, merge, conflict, idempotency events)

The design follows the assignment requirements: no hallucination, strict evidence-based extraction, clear versioning (v1 from demo, v2 from onboarding), safe partial merges, and idempotent batch processing.

### Repository Layout

- `data/raw/` – input transcripts  
  - `bens_electric_demo.txt` – demo call transcript (v1 source)  
  - `bens_electric_onboarding.txt` – onboarding call transcript (v2 source)
- `scripts/` – Python scripts for extraction, merging, and utilities
- `workflows/` – n8n (or equivalent) workflow exports (JSON) and docs
- `outputs/accounts/<account_id>/v1/` – v1 memo + agent spec
- `outputs/accounts/<account_id>/v2/` – v2 memo + agent spec
- `changelog/<account_id>.json` – append-only changelog for this account
- `logs/<account_id>.log` – plain-text log for this account

### Quick Start

Requirements:

- Python 3.10+

Install dependencies (none external yet; kept for future extension):

```bash
pip install -r requirements.txt
```

Run the pipeline from the repo root:

```bash
cd scripts
python3 run_pipeline.py
cd ..
```

This will:

1. Ingest demo transcripts from `data/raw/*_demo.txt` and create **v1** artifacts.  
2. Ingest onboarding transcripts from `data/raw/*_onboarding.txt` and create or update **v2** artifacts.  
3. Enforce **idempotency** using deterministic `account_id` and content hashes.  
4. Write logs to `logs/<account_id>.log` and changelogs to `changelog/<account_id>.json`.

See `scripts/schema.py` and `scripts/run_pipeline.py` for the exact JSON shapes and merge rules.

### Diff viewer & summary metrics

To inspect how v2 differs from v1 for a given account and see coverage stats:

```bash
cd scripts
python3 diff_viewer.py <account_id>
```

Output includes:

- **Field coverage**: how many key fields are missing/unknown in v1 vs v2  
- **Updated fields**: which evidence-based fields changed from v1 → v2 and their before/after values

You can find `<account_id>` by listing `outputs/accounts/` after a run.

### n8n workflow (optional)

The `workflows/n8n_clara_pipeline.json` file is an exportable n8n workflow that:

- Starts from a **Manual Trigger** node  
- Runs a single **Execute Command** node to call:
  - `cd /data/clara-automation-pipeline && cd scripts && python3 run_pipeline.py`

Suggested usage:

1. Mount this repo into your n8n container at `/data/clara-automation-pipeline`.  
2. Import `workflows/n8n_clara_pipeline.json` into n8n.  
3. Manually trigger the workflow to process all available demo + onboarding transcripts.

### Task Tracking Layer

This project includes a minimal, zero-cost task tracking layer under:

- `tasks/<account_id>.json`

Each file acts as a mock task record (similar to an Asana ticket) with:

- `account_id`
- `status` (for example: `v1_generated`, `onboarding_updated`)
- `source` (`demo_call` or `onboarding_call`)
- `created_at` / `updated_at` (ISO8601, UTC)

The pipeline automatically upserts these files when v1 or v2 artifacts are created, giving you a simple, local way to track per-account workflow state without any paid SaaS.

### Notes

- All extraction is **evidence-based**: every field stores `value`, `confidence` (`explicit | implied | missing`), and `source_quote`.  
- Missing or ambiguous fields are left `null` and surfaced in `questions_or_unknowns`.  
- File writes are **atomic** (temp file + rename) and JSON is schema-validated before commit.

