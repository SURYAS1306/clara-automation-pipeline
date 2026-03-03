from __future__ import annotations

"""
Core data schemas and helper utilities for the Clara automation pipeline.

The key design requirement is **evidence-based extraction**:
every extracted field is represented as:

{
    "value": ...,
    "confidence": "explicit" | "implied" | "missing",
    "source_quote": "exact snippet from transcript or ''"
}

If a field has no supporting evidence, `value` is None, `confidence` is "missing",
and `source_quote` is "" (and the caller should also add an entry to
`questions_or_unknowns` in the memo).
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Literal, TypedDict


Confidence = Literal["explicit", "implied", "missing"]


class EvidenceField(TypedDict, total=False):
    value: Any
    confidence: Confidence
    source_quote: str


def evidence_missing() -> EvidenceField:
    return {"value": None, "confidence": "missing", "source_quote": ""}


def evidence_explicit(value: Any, source_quote: str) -> EvidenceField:
    return {"value": value, "confidence": "explicit", "source_quote": source_quote}


def evidence_implied(value: Any, source_quote: str) -> EvidenceField:
    return {"value": value, "confidence": "implied", "source_quote": source_quote}


class MemoJSON(TypedDict):
    account_id: str
    # company_name is an EvidenceField to keep source metadata;
    # callers can also use company_name["value"] for plain string.
    company_name: EvidenceField
    business_hours: EvidenceField  # expects dict with days/start/end/timezone
    office_address: EvidenceField
    services_supported: EvidenceField  # list of strings
    emergency_definition: EvidenceField  # list of strings
    emergency_routing_rules: EvidenceField  # dict structure
    non_emergency_routing_rules: EvidenceField
    call_transfer_rules: EvidenceField
    integration_constraints: EvidenceField
    after_hours_flow_summary: EvidenceField
    office_hours_flow_summary: EvidenceField
    questions_or_unknowns: List[str]
    notes: str
    version: str  # "v1" or "v2"
    source: Literal["demo_call", "onboarding_call"]


class AgentSpecJSON(TypedDict):
    account_id: str
    company_name: str | None
    agent_name: str
    voice_style: str
    system_prompt: str
    key_variables: Dict[str, Any]
    call_transfer_protocol: str
    fallback_protocol: str
    version: str  # "v1" or "v2"
    source: Literal["demo_call", "onboarding_call"]


class ChangeEntry(TypedDict):
    field: str
    previous_value: Any
    new_value: Any
    conflict_type: Optional[str]
    resolution_source: str
    note: str


class ChangelogJSON(TypedDict):
    account_id: str
    company_name: str | None
    version: str
    entries: List[ChangeEntry]


def validate_core_fields(obj: Dict[str, Any]) -> None:
    """
    Validate that required top-level fields exist before writing JSON.
    Raises ValueError on failure.
    """
    missing = [k for k in ("account_id", "company_name", "version") if k not in obj]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

