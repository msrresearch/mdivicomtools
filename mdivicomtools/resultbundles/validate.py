from __future__ import annotations

from typing import Any, Dict, Optional

from .types import ResolvedSidecar, ValidationReport


VALIDATION_MODES = {"strict", "warn", "off"}


def parse_validation_mode(mode: str) -> str:
    normalized = (mode or "strict").strip().lower()
    if normalized not in VALIDATION_MODES:
        raise ValueError(f"Unsupported validation mode '{mode}'. Expected one of: {', '.join(sorted(VALIDATION_MODES))}.")
    return normalized


def _validate_time_reference(report: ValidationReport, value: Any) -> None:
    if not isinstance(value, dict):
        report.add_error("time_reference must be an object.")
        return
    for key in ("kind", "unit"):
        current = value.get(key)
        if not isinstance(current, str) or not current.strip():
            report.add_error(f"time_reference.{key} must be a non-empty string.")


def _validate_source(report: ValidationReport, value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        report.add_error("source must be an object when present.")
        return
    for key in ("root", "root_base"):
        current = value.get(key)
        if not isinstance(current, str) or not current.strip():
            report.add_error(f"source.{key} must be a non-empty string when source is present.")

    root_base = value.get("root_base")
    if isinstance(root_base, str) and root_base.strip():
        normalized_root_base = root_base.strip().lower()
        if normalized_root_base not in {"dataset_dir", "out_dir"}:
            report.add_warning(
                f"source.root_base='{root_base}' is non-portable; prefer 'dataset_dir' or 'out_dir' for external handoff."
            )


def _validate_files_structure(report: ValidationReport, files_value: Any) -> None:
    if not isinstance(files_value, list):
        report.add_error("files must be an array.")
        return
    if not files_value:
        report.add_error("files must contain at least one entry.")
        return

    for idx, entry in enumerate(files_value):
        if not isinstance(entry, dict):
            report.add_error(f"files[{idx}] must be an object.")
            continue
        for key in ("path", "role", "format", "required"):
            if key not in entry:
                report.add_error(f"files[{idx}] is missing required key '{key}'.")
        path_value = entry.get("path")
        if path_value is not None and (not isinstance(path_value, str) or not path_value.strip()):
            report.add_error(f"files[{idx}].path must be a non-empty string.")
        role_value = entry.get("role")
        if role_value is not None and (not isinstance(role_value, str) or not role_value.strip()):
            report.add_error(f"files[{idx}].role must be a non-empty string.")
        format_value = entry.get("format")
        if format_value is not None and (not isinstance(format_value, str) or not format_value.strip()):
            report.add_error(f"files[{idx}].format must be a non-empty string.")

        required_value = entry.get("required")
        if required_value is None:
            continue
        if isinstance(required_value, bool):
            continue
        report.add_error(f"files[{idx}].required must be a boolean.")


def validate_envelope(
    sidecar: Dict[str, Any],
    *,
    mode: str = "strict",
    resolved: Optional[ResolvedSidecar] = None,
) -> ValidationReport:
    normalized_mode = parse_validation_mode(mode)
    report = ValidationReport(mode=normalized_mode)

    if normalized_mode == "off":
        report.add_note("Validation mode is off; envelope checks were skipped.")
        return report

    if not isinstance(sidecar, dict):
        report.add_error("Sidecar content must be an object.")
        return report

    for key in ("resultbundle_type", "schema_version", "time_reference", "files"):
        if key not in sidecar:
            report.add_error(f"Missing required top-level key '{key}'.")

    resultbundle_type = sidecar.get("resultbundle_type")
    if resultbundle_type is not None and (not isinstance(resultbundle_type, str) or not resultbundle_type.strip()):
        report.add_error("resultbundle_type must be a non-empty string.")

    schema_version = sidecar.get("schema_version")
    if schema_version is not None and (not isinstance(schema_version, str) or not schema_version.strip()):
        report.add_error("schema_version must be a non-empty string.")

    if "time_reference" in sidecar:
        _validate_time_reference(report, sidecar.get("time_reference"))

    if "files" in sidecar:
        _validate_files_structure(report, sidecar.get("files"))

    _validate_source(report, sidecar.get("source"))

    if resolved is not None:
        for warning in resolved.warnings:
            report.add_warning(warning)
        for issue in resolved.issues:
            if normalized_mode == "strict":
                report.add_error(issue)
            else:
                report.add_warning(issue)

        source = sidecar.get("source")
        if isinstance(source, dict):
            root_base = source.get("root_base")
            if isinstance(root_base, str) and root_base.strip():
                normalized_root_base = root_base.strip().lower()
                if normalized_mode == "strict" and normalized_root_base not in {"dataset_dir", "out_dir"}:
                    report.add_error(
                        f"source.root_base='{root_base}' is not allowed in strict mode; use 'dataset_dir' or 'out_dir'."
                    )

        for file_item in resolved.files:
            if file_item.required and not file_item.exists:
                message = f"Required file is missing: {file_item.declared_path} (resolved: {file_item.resolved_path})"
                if normalized_mode == "strict":
                    report.add_error(message)
                else:
                    report.add_warning(message)

    return report
