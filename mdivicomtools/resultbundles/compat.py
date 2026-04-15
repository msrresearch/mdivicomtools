from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

from .types import CompatibilityDecision


_SEMVER_RE = re.compile(r"^\s*(\d+)\.(\d+)(?:\.(\d+))?(?:[-+].*)?\s*$")


def _parse_schema_version(version: str) -> Tuple[int, int, int]:
    match = _SEMVER_RE.match(version or "")
    if not match:
        raise ValueError(f"Invalid schema_version '{version}'. Expected SemVer-like version (for example 0.1.0).")
    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3) or 0)
    return major, minor, patch


def check_compatibility(
    sidecar: Dict[str, Any],
    *,
    expected_type: str,
    supported_major: Optional[int] = None,
    min_minor: Optional[int] = None,
) -> CompatibilityDecision:
    provided_type = sidecar.get("resultbundle_type")
    schema_version = sidecar.get("schema_version")

    if not isinstance(provided_type, str) or not provided_type:
        return CompatibilityDecision(
            compatible=False,
            level="incompatible",
            reason="Missing or invalid resultbundle_type in sidecar.",
            expected_type=expected_type,
            provided_type=str(provided_type) if provided_type is not None else None,
            schema_version=str(schema_version) if schema_version is not None else None,
        )

    if provided_type != expected_type:
        return CompatibilityDecision(
            compatible=False,
            level="incompatible",
            reason=f"resultbundle_type mismatch: expected '{expected_type}', got '{provided_type}'.",
            expected_type=expected_type,
            provided_type=provided_type,
            schema_version=str(schema_version) if schema_version is not None else None,
        )

    if not isinstance(schema_version, str) or not schema_version:
        return CompatibilityDecision(
            compatible=False,
            level="incompatible",
            reason="Missing or invalid schema_version in sidecar.",
            expected_type=expected_type,
            provided_type=provided_type,
            schema_version=str(schema_version) if schema_version is not None else None,
        )

    try:
        major, minor, _patch = _parse_schema_version(schema_version)
    except ValueError as exc:
        return CompatibilityDecision(
            compatible=False,
            level="incompatible",
            reason=str(exc),
            expected_type=expected_type,
            provided_type=provided_type,
            schema_version=schema_version,
        )

    if supported_major is not None and major != supported_major:
        return CompatibilityDecision(
            compatible=False,
            level="incompatible",
            reason=f"schema_version major mismatch: supported {supported_major}, got {major}.",
            expected_type=expected_type,
            provided_type=provided_type,
            schema_version=schema_version,
        )

    if min_minor is not None and minor < min_minor:
        return CompatibilityDecision(
            compatible=True,
            level="warn",
            reason=f"schema_version minor is older than preferred minimum: expected >= {min_minor}, got {minor}.",
            expected_type=expected_type,
            provided_type=provided_type,
            schema_version=schema_version,
        )

    return CompatibilityDecision(
        compatible=True,
        level="compatible",
        reason="resultbundle_type and schema_version are compatible with current policy.",
        expected_type=expected_type,
        provided_type=provided_type,
        schema_version=schema_version,
    )
