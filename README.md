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



### How to Run From Scratch

1. Clone the repository.
2. Ensure Python 3.10+ is installed.
3. Place demo and onboarding transcripts inside `data/raw/`.
4. Run:

   ```
   cd scripts
   python3 run_pipeline.py
   cd ..
   ```

All outputs will be generated under:

- `outputs/accounts/`
- `changelog/`
- `logs/`
- `tasks/`

No external services or paid APIs are required.

---


### Account Memo Schema (Required Fields)

Each account memo (`memo.json`) contains the required structured fields:

- `account_id`
- `company_name`
- `business_hours` (days, start, end, timezone)
- `office_address`
- `services_supported`
- `emergency_definition`
- `emergency_routing_rules`
- `non_emergency_routing_rules`
- `call_transfer_rules`
- `integration_constraints`
- `after_hours_flow_summary`
- `office_hours_flow_summary`
- `questions_or_unknowns`
- `notes`
- `version`

Each field includes:

- `value`
- `confidence` (`explicit | implied | missing`)
- `source_quote`

No fields are hallucinated. Missing data is preserved explicitly.

---

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

### Batch Processing (5 Demo + 5 Onboarding Support)

The pipeline automatically processes **all matching files** in `data/raw/`:

- `*_demo.txt` → generates `v1` artifacts  
- `*_onboarding.txt` → generates or updates `v2` artifacts  

This enables end-to-end execution on datasets containing **5 demo calls + 5 onboarding calls** (or more) in a single run.

The workflow is deterministic and idempotent — running it multiple times does not create duplicate artifacts or inconsistent state.

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

---

### n8n workflow (optional)

The `workflows/n8n_clara_pipeline.json` file is an exportable n8n workflow that:

- Starts from a **Manual Trigger** node  
- Runs a single **Execute Command** node to call:
  - `cd /data/clara-automation-pipeline && cd scripts && python3 run_pipeline.py`

Suggested usage:

1. Mount this repo into your n8n container at `/data/clara-automation-pipeline`.  
2. Import `workflows/n8n_clara_pipeline.json` into n8n.  
3. Manually trigger the workflow to process all available demo + onboarding transcripts.

---

### Retell Setup

This project generates a **Retell Agent Draft Spec** (`agent_spec.json`) for each account.  
The spec represents how the Clara Answers agent would be configured inside Retell.

Because this assignment requires **zero spend**, the pipeline does not automatically call Retell APIs.  
Instead, it produces a fully structured agent configuration that can be manually imported.

#### Create a Retell Account

- Sign up at https://retellai.com  
- Create a new agent from the dashboard  
- If available on the free tier, generate an API key from the Retell dashboard  

*(API usage is optional and not required for this project.)*

#### Manual Import Steps

For each account:

1. Run the pipeline.  
2. Open:
   - `outputs/accounts/<account_id>/v1/agent_spec.json`
   - `outputs/accounts/<account_id>/v2/agent_spec.json`
3. In the Retell dashboard:
   - Create or edit an agent  
   - Copy the generated **system prompt** into the prompt section  
   - Configure business hours, routing rules, and transfer settings using the JSON as reference  
4. Save the agent.

---

#### Versioning

- `v1` → Generated from demo call (preliminary configuration)  
- `v2` → Updated after onboarding call (operationally confirmed rules)

The JSON files serve as the source of truth and allow full reproducibility even without API access.

---

### Task Tracking Layer

This project includes a minimal, zero-cost task tracking layer under:

- `tasks/<account_id>.json`

Each file acts as a mock task record (similar to an Asana ticket) with:

- `account_id`
- `status` (for example: `v1_generated`, `onboarding_updated`)
- `source` (`demo_call` or `onboarding_call`)
- `created_at` / `updated_at` (ISO8601, UTC)

The pipeline automatically upserts these files when v1 or v2 artifacts are created, giving you a simple, local way to track per-account workflow state without any paid SaaS.

---

### LLM Usage (Zero-Cost Compliance)

This implementation uses deterministic rule-based extraction and structured templating.

No external LLM APIs are called.
No paid inference services are required.

All parsing and agent spec generation is performed locally using Python logic, ensuring full compliance with the zero-cost constraint.

### Notes

- All extraction is **evidence-based**: every field stores `value`, `confidence` (`explicit | implied | missing`), and `source_quote`.  
- Missing or ambiguous fields are left `null` and surfaced in `questions_or_unknowns`.  
- File writes are **atomic** (temp file + rename) and JSON is schema-validated before commit.

