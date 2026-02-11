from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


def new_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rand = secrets.token_hex(4)
    return f"{ts}_{rand}"


def _stable_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def config_hash(config: Any) -> str:
    return hashlib.sha256(_stable_json(config).encode("utf-8")).hexdigest()


def run_record(*, plugin: Dict[str, Any], dataset_dir: Path, out_dir: Path, work_dir: Optional[Path], config: Dict[str, Any], backend: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "run_id": None,  # filled by writer
        "created_at": now,
        "plugin": {
            "id": plugin.get("id"),
            "publisher": plugin.get("publisher"),
            "kind": plugin.get("kind"),
            "version": plugin.get("version"),
            "entry_point": plugin.get("entry_point"),
        },
        "backend": backend,
        "dataset_dir": str(dataset_dir),
        "out_dir": str(out_dir),
        "work_dir": str(work_dir) if work_dir else None,
        "config_hash_sha256": config_hash(config),
    }


def write_run_record(out_dir: Path, run_id: str, record: Dict[str, Any]) -> Path:
    runs_dir = out_dir / "_runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    record = dict(record)
    record["run_id"] = run_id
    path = runs_dir / f"{run_id}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    return path
