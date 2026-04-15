from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ValidationPolicy:
    name: str
    validation_mode: str
    allow_fallback: bool
    require_fallback_reason: bool
    description: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


_POLICIES: Dict[str, ValidationPolicy] = {
    "local_default": ValidationPolicy(
        name="local_default",
        validation_mode="off",
        allow_fallback=True,
        require_fallback_reason=False,
        description="Legacy/local mode: keep CSV-first behavior, skip strict bundle checks.",
    ),
    "plugin_strict": ValidationPolicy(
        name="plugin_strict",
        validation_mode="strict",
        allow_fallback=False,
        require_fallback_reason=False,
        description="Plugin/pipeline external handoff mode: validate strictly and fail fast.",
    ),
    "pipeline_auto": ValidationPolicy(
        name="pipeline_auto",
        validation_mode="warn",
        allow_fallback=True,
        require_fallback_reason=True,
        description="Auto mode: warn-level validation; callers may fallback but must persist a reason.",
    ),
    "legacy_off": ValidationPolicy(
        name="legacy_off",
        validation_mode="off",
        allow_fallback=True,
        require_fallback_reason=False,
        description="Compatibility mode for legacy paths where bundle validation is intentionally disabled.",
    ),
}


def list_validation_policies() -> Dict[str, ValidationPolicy]:
    return dict(_POLICIES)


def get_validation_policy(name: str) -> ValidationPolicy:
    key = (name or "").strip().lower()
    if key not in _POLICIES:
        supported = ", ".join(sorted(_POLICIES))
        raise ValueError(f"Unsupported validation policy '{name}'. Supported policies: {supported}.")
    return _POLICIES[key]


def select_validation_mode(*, mode: Optional[str], policy: Optional[str], default_mode: str = "strict") -> str:
    if mode is not None:
        return mode
    if policy is not None:
        return get_validation_policy(policy).validation_mode
    return default_mode
