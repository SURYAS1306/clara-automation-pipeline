from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT / "outputs" / "accounts"


EVIDENCE_FIELDS = [
    "company_name",
    "business_hours",
    "office_address",
    "services_supported",
    "emergency_definition",
    "emergency_routing_rules",
    "non_emergency_routing_rules",
    "call_transfer_rules",
    "integration_constraints",
    "after_hours_flow_summary",
    "office_hours_flow_summary",
]


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def summarize_missing_fields(memo: Dict[str, Any]) -> int:
    missing = 0
    for field in EVIDENCE_FIELDS:
        ev = memo.get(field, {})
        if not isinstance(ev, dict):
            continue
        if ev.get("confidence") == "missing" or ev.get("value") is None:
            missing += 1
    return missing


def diff_values(v1: Any, v2: Any) -> bool:
    return v1 != v2


def compute_diff(v1_memo: Dict[str, Any], v2_memo: Dict[str, Any]) -> List[Tuple[str, Any, Any]]:
    diffs: List[Tuple[str, Any, Any]] = []
    for field in EVIDENCE_FIELDS:
        ev1 = v1_memo.get(field, {})
        ev2 = v2_memo.get(field, {})
        v1_val = ev1.get("value") if isinstance(ev1, dict) else ev1
        v2_val = ev2.get("value") if isinstance(ev2, dict) else ev2
        if diff_values(v1_val, v2_val):
            diffs.append((field, v1_val, v2_val))
    return diffs


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python3 diff_viewer.py <account_id>", file=sys.stderr)
        sys.exit(1)

    account_id = sys.argv[1]
    v1_path = OUTPUTS_DIR / account_id / "v1" / "memo.json"
    v2_path = OUTPUTS_DIR / account_id / "v2" / "memo.json"

    if not v1_path.exists() or not v2_path.exists():
        print(f"Missing v1 or v2 memo for account_id={account_id}", file=sys.stderr)
        sys.exit(1)

    v1_memo = load_json(v1_path)
    v2_memo = load_json(v2_path)

    total_fields = len(EVIDENCE_FIELDS)
    v1_missing = summarize_missing_fields(v1_memo)
    v2_missing = summarize_missing_fields(v2_memo)
    diffs = compute_diff(v1_memo, v2_memo)

    print(f"Account: {account_id}")
    print(f"Company: {v1_memo.get('company_name', {}).get('value')}")
    print()
    print("=== Field Coverage ===")
    print(f"Total evidence-based fields: {total_fields}")
    print(f"v1 missing/unknown fields: {v1_missing} ({v1_missing/total_fields:.0%})")
    print(f"v2 missing/unknown fields: {v2_missing} ({v2_missing/total_fields:.0%})")
    print()
    print("=== Updated Fields (v1 -> v2) ===")
    if not diffs:
        print("No field-level changes detected.")
    else:
        for field, before, after in diffs:
            print(f"- {field}:")
            print(f"    v1: {before}")
            print(f"    v2: {after}")


if __name__ == "__main__":
    main()

