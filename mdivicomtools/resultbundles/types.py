from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ResolvedFile:
    declared_path: str
    resolved_path: str
    role: str
    format: str
    required: bool
    exists: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResolvedSidecar:
    sidecar_path: str
    payload_root: str
    detached: bool
    sidecar: Dict[str, Any]
    source: Optional[Dict[str, Any]]
    files: List[ResolvedFile] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sidecar_path": self.sidecar_path,
            "payload_root": self.payload_root,
            "detached": self.detached,
            "resultbundle_type": self.sidecar.get("resultbundle_type"),
            "schema_version": self.sidecar.get("schema_version"),
            "source": self.source,
            "files": [item.to_dict() for item in self.files],
            "issues": list(self.issues),
            "warnings": list(self.warnings),
        }


@dataclass
class ValidationReport:
    mode: str
    valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_note(self, message: str) -> None:
        self.notes.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "notes": list(self.notes),
        }


@dataclass
class CompatibilityDecision:
    compatible: bool
    level: str
    reason: str
    expected_type: Optional[str] = None
    provided_type: Optional[str] = None
    schema_version: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "compatible": self.compatible,
            "level": self.level,
            "reason": self.reason,
            "expected_type": self.expected_type,
            "provided_type": self.provided_type,
            "schema_version": self.schema_version,
        }
