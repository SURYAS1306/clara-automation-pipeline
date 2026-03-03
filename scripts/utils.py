from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from schema import validate_core_fields

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = ROOT / "outputs" / "accounts"
CHANGELOG_DIR = ROOT / "changelog"
LOGS_DIR = ROOT / "logs"
TASKS_DIR = ROOT / "tasks"


def ensure_dirs_for_account(account_id: str) -> None:
    (OUTPUTS_DIR / account_id / "v1").mkdir(parents=True, exist_ok=True)
    (OUTPUTS_DIR / account_id / "v2").mkdir(parents=True, exist_ok=True)
    CHANGELOG_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)


def deterministic_account_id(company_name: str | None, demo_filename: str) -> str:
    """
    Deterministic account_id per spec:

    hash(company_name + demo_filename)

    If company_name is missing, we still include the literal string "UNKNOWN"
    so the id is stable.
    """
    base_name = Path(demo_filename).stem
    key = f"{company_name or 'UNKNOWN'}::{base_name}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    # A human-readable slug helps debugging
    slug = base_name.replace("_demo", "").replace("_", "-")
    return f"{slug}-{digest}"


def compute_json_checksum(obj: Dict[str, Any]) -> str:
    """Stable JSON checksum used for idempotency."""
    data = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def atomic_write_json(path: Path, obj: Dict[str, Any]) -> None:
    """
    Write JSON to a temp file and atomically replace the target.
    Validates required schema fields first.
    """
    validate_core_fields(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        dir=str(path.parent), prefix=".tmp_", suffix=".json"
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


def append_log(account_id: str, message: str) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    path = LOGS_DIR / f"{account_id}.log"
    with path.open("a", encoding="utf-8") as f:
        f.write(message.rstrip() + "\n")


def upsert_task_status(account_id: str, status: str, source: str) -> None:
    """
    Minimal zero-cost task tracking layer.

    Creates or updates /tasks/<account_id>.json with:
    {
      "account_id": "...",
      "status": status,
      "source": source,
      "created_at": ISO8601,
      "updated_at": ISO8601
    }
    """
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    task_path = TASKS_DIR / f"{account_id}.json"
    now = datetime.now(timezone.utc).isoformat()

    if task_path.exists():
        try:
            data = json.loads(task_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {"account_id": account_id, "created_at": now}
        created_at = data.get("created_at", now)
    else:
        data = {"account_id": account_id}
        created_at = now

    data.update(
        {
            "account_id": account_id,
            "status": status,
            "source": source,
            "created_at": created_at,
            "updated_at": now,
        }
    )

    task_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        dir=str(task_path.parent), prefix=".tmp_task_", suffix=".json"
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, task_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

