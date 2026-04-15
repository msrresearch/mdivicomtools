from __future__ import annotations

import json
from pathlib import Path

import pytest

from mdivicomtools.resultbundles.compat import check_compatibility
from mdivicomtools.resultbundles.policy import (
    get_validation_policy,
    list_validation_policies,
    select_validation_mode,
)
from mdivicomtools.resultbundles.resolve import ResultBundleResolutionError, resolve_sidecar
from mdivicomtools.resultbundles.validate import validate_envelope


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_resolve_detached_sidecar_with_out_dir_root_base(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    payload_root = out_dir / "payload"
    payload_root.mkdir(parents=True, exist_ok=True)
    (payload_root / "timeline.csv").write_text("time_s,wearer\n0.0,sub-01\n", encoding="utf-8")

    sidecar_path = out_dir / "resultbundles" / "timeline" / "resultbundle.json"
    sidecar = {
        "resultbundle_type": "mdivicom.timeline.subject",
        "schema_version": "0.1.0",
        "time_reference": {"kind": "timestamp", "unit": "ns"},
        "source": {"root": "payload", "root_base": "out_dir"},
        "files": [
            {
                "path": "timeline.csv",
                "role": "timeline",
                "format": "text/csv",
                "required": True,
            }
        ],
    }
    _write_json(sidecar_path, sidecar)

    resolved = resolve_sidecar(sidecar_path, out_dir=out_dir)
    assert Path(resolved.payload_root) == payload_root.resolve()
    assert len(resolved.files) == 1
    assert resolved.files[0].exists is True


def test_resolve_rejects_path_escape_in_strict_mode(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    payload_root = out_dir / "payload"
    payload_root.mkdir(parents=True, exist_ok=True)

    sidecar_path = out_dir / "resultbundles" / "bad" / "resultbundle.json"
    sidecar = {
        "resultbundle_type": "mdivicom.timeline.subject",
        "schema_version": "0.1.0",
        "time_reference": {"kind": "timestamp", "unit": "ns"},
        "source": {"root": "payload", "root_base": "out_dir"},
        "files": [
            {
                "path": "../secret.csv",
                "role": "timeline",
                "format": "text/csv",
                "required": True,
            }
        ],
    }
    _write_json(sidecar_path, sidecar)

    with pytest.raises(ResultBundleResolutionError):
        resolve_sidecar(sidecar_path, out_dir=out_dir, strict=True)


def test_resolve_rejects_source_root_escape_in_strict_mode(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    payload_root = tmp_path / "payload"
    payload_root.mkdir(parents=True, exist_ok=True)
    (payload_root / "timeline.csv").write_text("time_s,wearer\n0.0,sub-01\n", encoding="utf-8")

    sidecar_path = out_dir / "resultbundles" / "bad-root" / "resultbundle.json"
    sidecar = {
        "resultbundle_type": "mdivicom.timeline.subject",
        "schema_version": "0.1.0",
        "time_reference": {"kind": "timestamp", "unit": "ns"},
        "source": {"root": "../payload", "root_base": "out_dir"},
        "files": [
            {
                "path": "timeline.csv",
                "role": "timeline",
                "format": "text/csv",
                "required": True,
            }
        ],
    }
    _write_json(sidecar_path, sidecar)

    with pytest.raises(ResultBundleResolutionError, match="source.root escapes"):
        resolve_sidecar(sidecar_path, out_dir=out_dir, strict=True)


def test_resolve_rejects_absolute_source_root_in_strict_mode(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    payload_root = tmp_path / "payload"
    payload_root.mkdir(parents=True, exist_ok=True)
    (payload_root / "timeline.csv").write_text("time_s,wearer\n0.0,sub-01\n", encoding="utf-8")

    sidecar_path = out_dir / "resultbundles" / "bad-root-absolute" / "resultbundle.json"
    sidecar = {
        "resultbundle_type": "mdivicom.timeline.subject",
        "schema_version": "0.1.0",
        "time_reference": {"kind": "timestamp", "unit": "ns"},
        "source": {"root": str(payload_root), "root_base": "out_dir"},
        "files": [
            {
                "path": "timeline.csv",
                "role": "timeline",
                "format": "text/csv",
                "required": True,
            }
        ],
    }
    _write_json(sidecar_path, sidecar)

    with pytest.raises(ResultBundleResolutionError, match="source.root must be relative"):
        resolve_sidecar(sidecar_path, out_dir=out_dir, strict=True)


def test_resolve_normalizes_legacy_root_base_aliases(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    payload_root = out_dir / "payload"
    payload_root.mkdir(parents=True, exist_ok=True)
    (payload_root / "timeline.csv").write_text("time_s,wearer\n0.0,sub-01\n", encoding="utf-8")

    sidecar_path = out_dir / "resultbundles" / "timeline" / "resultbundle.json"
    sidecar = {
        "resultbundle_type": "mdivicom.timeline.subject",
        "schema_version": "0.1.0",
        "time_reference": {"kind": "timestamp", "unit": "ns"},
        "source": {"root": "payload", "root_base": "output_data_dir"},
        "files": [
            {
                "path": "timeline.csv",
                "role": "timeline",
                "format": "text/csv",
                "required": True,
            }
        ],
    }
    _write_json(sidecar_path, sidecar)

    resolved = resolve_sidecar(sidecar_path, out_dir=out_dir)
    assert resolved.source is not None
    assert resolved.source.get("root_base") == "out_dir"
    assert any("output_data_dir" in warning for warning in resolved.warnings)


def test_resolve_normalizes_payload_provenance_to_upstream_tool(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    payload_root = out_dir / "payload"
    payload_root.mkdir(parents=True, exist_ok=True)
    (payload_root / "timeline.csv").write_text("time_s,wearer\n0.0,sub-01\n", encoding="utf-8")

    sidecar_path = out_dir / "resultbundles" / "timeline" / "resultbundle.json"
    sidecar = {
        "resultbundle_type": "mdivicom.timeline.subject",
        "schema_version": "0.1.0",
        "time_reference": {"kind": "timestamp", "unit": "ns"},
        "payload_provenance": {"tool_ref": "pupilcloud/raw-data-exporter", "tool_version": "4"},
        "source": {"root": "payload", "root_base": "out_dir"},
        "files": [
            {
                "path": "timeline.csv",
                "role": "timeline",
                "format": "text/csv",
                "required": True,
            }
        ],
    }
    _write_json(sidecar_path, sidecar)

    resolved = resolve_sidecar(sidecar_path, out_dir=out_dir)
    assert "upstream_tool" in resolved.sidecar
    assert "payload_provenance" not in resolved.sidecar
    assert any("payload_provenance" in warning and "upstream_tool" in warning for warning in resolved.warnings)


def test_resolve_non_strict_reports_non_portable_source_root_issues(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    payload_root = tmp_path / "payload"
    payload_root.mkdir(parents=True, exist_ok=True)
    (payload_root / "timeline.csv").write_text("time_s,wearer\n0.0,sub-01\n", encoding="utf-8")

    escape_sidecar_path = out_dir / "resultbundles" / "warn-root" / "resultbundle.json"
    escape_sidecar = {
        "resultbundle_type": "mdivicom.timeline.subject",
        "schema_version": "0.1.0",
        "time_reference": {"kind": "timestamp", "unit": "ns"},
        "source": {"root": "../payload", "root_base": "out_dir"},
        "files": [
            {
                "path": "timeline.csv",
                "role": "timeline",
                "format": "text/csv",
                "required": True,
            }
        ],
    }
    _write_json(escape_sidecar_path, escape_sidecar)

    resolved_escape = resolve_sidecar(escape_sidecar_path, out_dir=out_dir, strict=False)
    report_escape = validate_envelope(resolved_escape.sidecar, mode="warn", resolved=resolved_escape)
    assert Path(resolved_escape.payload_root) == payload_root.resolve()
    assert report_escape.valid is True
    assert any("source.root escapes" in warning for warning in report_escape.warnings)

    absolute_sidecar_path = out_dir / "resultbundles" / "warn-root-absolute" / "resultbundle.json"
    absolute_sidecar = {
        "resultbundle_type": "mdivicom.timeline.subject",
        "schema_version": "0.1.0",
        "time_reference": {"kind": "timestamp", "unit": "ns"},
        "source": {"root": str(payload_root), "root_base": "out_dir"},
        "files": [
            {
                "path": "timeline.csv",
                "role": "timeline",
                "format": "text/csv",
                "required": True,
            }
        ],
    }
    _write_json(absolute_sidecar_path, absolute_sidecar)

    resolved_absolute = resolve_sidecar(absolute_sidecar_path, out_dir=out_dir, strict=False)
    report_absolute = validate_envelope(resolved_absolute.sidecar, mode="warn", resolved=resolved_absolute)
    assert Path(resolved_absolute.payload_root) == payload_root.resolve()
    assert report_absolute.valid is True
    assert any("source.root must be relative" in warning for warning in report_absolute.warnings)


def test_validate_strict_mode_rejects_non_portable_root_base(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    payload_root = tmp_path / "payload"
    payload_root.mkdir(parents=True, exist_ok=True)
    (payload_root / "timeline.csv").write_text("time_s,wearer\n0.0,sub-01\n", encoding="utf-8")

    sidecar_path = out_dir / "resultbundles" / "timeline" / "resultbundle.json"
    sidecar = {
        "resultbundle_type": "mdivicom.timeline.subject",
        "schema_version": "0.1.0",
        "time_reference": {"kind": "timestamp", "unit": "ns"},
        "source": {"root": str(payload_root), "root_base": "absolute"},
        "files": [
            {
                "path": "timeline.csv",
                "role": "timeline",
                "format": "text/csv",
                "required": True,
            }
        ],
    }
    _write_json(sidecar_path, sidecar)

    resolved = resolve_sidecar(sidecar_path, strict=False)
    report = validate_envelope(resolved.sidecar, mode="strict", resolved=resolved)
    assert report.valid is False
    assert any("not allowed in strict mode" in err and "absolute" in err for err in report.errors)


def test_validate_warn_mode_keeps_missing_required_file_non_fatal(tmp_path: Path) -> None:
    out_dir = tmp_path / "out"
    payload_root = out_dir / "payload"
    payload_root.mkdir(parents=True, exist_ok=True)

    sidecar_path = out_dir / "resultbundles" / "missing" / "resultbundle.json"
    sidecar = {
        "resultbundle_type": "mdivicom.timeline.subject",
        "schema_version": "0.1.0",
        "time_reference": {"kind": "timestamp", "unit": "ns"},
        "source": {"root": "payload", "root_base": "out_dir"},
        "files": [
            {
                "path": "does-not-exist.csv",
                "role": "timeline",
                "format": "text/csv",
                "required": True,
            }
        ],
    }
    _write_json(sidecar_path, sidecar)

    resolved = resolve_sidecar(sidecar_path, out_dir=out_dir, strict=False)
    report = validate_envelope(resolved.sidecar, mode="warn", resolved=resolved)
    assert report.valid is True
    assert report.warnings


def test_check_compatibility_major_mismatch_is_incompatible() -> None:
    decision = check_compatibility(
        {
            "resultbundle_type": "mdivicom.timeline.subject",
            "schema_version": "1.0.0",
        },
        expected_type="mdivicom.timeline.subject",
        supported_major=0,
    )
    assert decision.compatible is False
    assert decision.level == "incompatible"


def test_check_compatibility_older_minor_is_warn_level() -> None:
    decision = check_compatibility(
        {
            "resultbundle_type": "mdivicom.timeline.subject",
            "schema_version": "0.1.0",
        },
        expected_type="mdivicom.timeline.subject",
        supported_major=0,
        min_minor=2,
    )
    assert decision.compatible is True
    assert decision.level == "warn"


def test_validation_policy_profiles_include_expected_defaults() -> None:
    policies = list_validation_policies()
    assert {"local_default", "plugin_strict", "pipeline_auto", "legacy_off"}.issubset(set(policies))
    assert policies["plugin_strict"].validation_mode == "strict"
    assert policies["pipeline_auto"].allow_fallback is True
    assert policies["pipeline_auto"].require_fallback_reason is True


def test_select_validation_mode_prefers_explicit_mode_over_policy() -> None:
    assert select_validation_mode(mode="warn", policy="plugin_strict") == "warn"
    assert select_validation_mode(mode=None, policy="plugin_strict") == "strict"
    assert select_validation_mode(mode=None, policy=None) == "strict"


def test_get_validation_policy_rejects_unknown_policy() -> None:
    with pytest.raises(ValueError):
        get_validation_policy("not-a-policy")
