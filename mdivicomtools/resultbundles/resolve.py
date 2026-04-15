from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .types import ResolvedFile, ResolvedSidecar


class ResultBundleResolutionError(ValueError):
    pass


def _normalize_sidecar_inplace(sidecar: Dict[str, Any]) -> list[str]:
    warnings: list[str] = []

    if "upstream_tool" in sidecar:
        for legacy_key in ("payload_provenance", "upstream"):
            if legacy_key in sidecar:
                warnings.append(
                    f"Deprecated key '{legacy_key}' ignored because 'upstream_tool' is present. "
                    "Writers should emit 'upstream_tool' only."
                )
                sidecar.pop(legacy_key, None)
    else:
        if "upstream" in sidecar:
            sidecar["upstream_tool"] = sidecar.pop("upstream")
            warnings.append("Deprecated key 'upstream' treated as alias for 'upstream_tool'.")
        elif "payload_provenance" in sidecar:
            sidecar["upstream_tool"] = sidecar.pop("payload_provenance")
            warnings.append("Deprecated key 'payload_provenance' treated as alias for 'upstream_tool'.")

    source = sidecar.get("source")
    if isinstance(source, dict):
        root_base_raw = source.get("root_base")
        if isinstance(root_base_raw, str) and root_base_raw.strip():
            normalized = root_base_raw.strip().lower()
            legacy_root_bases = {
                "input_data_dir": "dataset_dir",
                "output_data_dir": "out_dir",
            }
            if normalized in legacy_root_bases:
                canonical = legacy_root_bases[normalized]
                source["root_base"] = canonical
                warnings.append(f"Deprecated source.root_base '{root_base_raw}' normalized to '{canonical}'.")
            elif normalized in {"dataset_dir", "out_dir", "cwd", "sidecar_dir", "absolute"}:
                source["root_base"] = normalized

    return warnings


def _coerce_optional_path(value: Optional[Union[str, Path]]) -> Optional[Path]:
    if value is None:
        return None
    return Path(value).expanduser().resolve(strict=False)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _resolve_payload_root(
    *,
    sidecar_path: Path,
    sidecar: Dict[str, Any],
    dataset_dir: Optional[Union[str, Path]],
    out_dir: Optional[Union[str, Path]],
    cwd: Optional[Union[str, Path]],
    strict: bool,
) -> tuple[Path, bool, Optional[Dict[str, Any]], list[str]]:
    source = sidecar.get("source")
    if not isinstance(source, dict):
        return sidecar_path.parent.resolve(strict=False), False, None, []

    root = source.get("root")
    root_base = source.get("root_base")

    if not isinstance(root, str) or not root.strip():
        raise ResultBundleResolutionError("Detached sidecar must define source.root as a non-empty string.")
    if not isinstance(root_base, str) or not root_base.strip():
        raise ResultBundleResolutionError("Detached sidecar must define source.root_base as a non-empty string.")

    normalized_root_base = root_base.strip().lower()
    base_map = {
        "dataset_dir": _coerce_optional_path(dataset_dir),
        "out_dir": _coerce_optional_path(out_dir),
        "cwd": _coerce_optional_path(cwd),
        "sidecar_dir": sidecar_path.parent.resolve(strict=False),
        "absolute": None,
    }

    if normalized_root_base not in base_map:
        raise ResultBundleResolutionError(
            f"Unsupported source.root_base '{root_base}'. Supported values: dataset_dir, out_dir, cwd, sidecar_dir, absolute."
        )

    issues: list[str] = []

    if normalized_root_base == "absolute":
        payload_root = Path(root).expanduser().resolve(strict=False)
    else:
        base = base_map[normalized_root_base]
        if base is None:
            raise ResultBundleResolutionError(
                f"source.root_base='{root_base}' requires the matching directory argument to be provided."
            )
        root_path = Path(root).expanduser()
        if root_path.is_absolute():
            message = (
                f"source.root must be relative to source.root_base='{normalized_root_base}' in strict mode: {root}"
            )
            if strict:
                raise ResultBundleResolutionError(message)
            issues.append(message)
            payload_root = root_path.resolve(strict=False)
        else:
            payload_root = (base / root_path).resolve(strict=False)
            if not _is_within(payload_root, base):
                message = f"source.root escapes source.root_base='{normalized_root_base}': {root}"
                if strict:
                    raise ResultBundleResolutionError(message)
                issues.append(message)

    return payload_root, True, source, issues


def resolve_sidecar(
    sidecar_path: Union[str, Path],
    *,
    dataset_dir: Optional[Union[str, Path]] = None,
    out_dir: Optional[Union[str, Path]] = None,
    cwd: Optional[Union[str, Path]] = None,
    strict: bool = True,
) -> ResolvedSidecar:
    sidecar_path = Path(sidecar_path).expanduser().resolve(strict=False)
    if not sidecar_path.exists():
        raise ResultBundleResolutionError(f"Sidecar does not exist: {sidecar_path}")
    if not sidecar_path.is_file():
        raise ResultBundleResolutionError(f"Sidecar path is not a file: {sidecar_path}")

    try:
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ResultBundleResolutionError(f"Could not parse sidecar JSON: {exc}") from exc

    if not isinstance(sidecar, dict):
        raise ResultBundleResolutionError("Sidecar JSON must be an object.")

    normalization_warnings = _normalize_sidecar_inplace(sidecar)

    payload_root, detached, source, source_issues = _resolve_payload_root(
        sidecar_path=sidecar_path,
        sidecar=sidecar,
        dataset_dir=dataset_dir,
        out_dir=out_dir,
        cwd=cwd,
        strict=strict,
    )

    files_raw = sidecar.get("files")
    if files_raw is None:
        files_raw = []
    if not isinstance(files_raw, list):
        raise ResultBundleResolutionError("Sidecar 'files' must be an array.")

    resolved = ResolvedSidecar(
        sidecar_path=str(sidecar_path),
        payload_root=str(payload_root),
        detached=detached,
        sidecar=sidecar,
        source=source,
        warnings=normalization_warnings,
    )
    resolved.issues.extend(source_issues)

    if detached and source is not None:
        root_base = source.get("root_base")
        if isinstance(root_base, str) and root_base.strip() and root_base.strip().lower() not in {"dataset_dir", "out_dir"}:
            resolved.warnings.append(
                f"source.root_base='{root_base}' is non-portable; prefer 'dataset_dir' or 'out_dir' for external handoff."
            )

    for idx, item in enumerate(files_raw):
        if not isinstance(item, dict):
            message = f"files[{idx}] must be an object."
            if strict:
                raise ResultBundleResolutionError(message)
            resolved.issues.append(message)
            continue

        declared = item.get("path")
        if not isinstance(declared, str) or not declared.strip():
            message = f"files[{idx}].path must be a non-empty string."
            if strict:
                raise ResultBundleResolutionError(message)
            resolved.issues.append(message)
            continue

        declared_path = Path(declared)
        if declared_path.is_absolute():
            resolved_path = declared_path.expanduser().resolve(strict=False)
            if strict:
                raise ResultBundleResolutionError(
                    f"files[{idx}].path must be relative to payload root in strict mode: {declared}"
                )
            resolved.issues.append(f"files[{idx}].path is absolute; portable relative paths are recommended.")
        else:
            resolved_path = (payload_root / declared_path).resolve(strict=False)
            if not _is_within(resolved_path, payload_root):
                message = f"files[{idx}].path escapes payload root: {declared}"
                if strict:
                    raise ResultBundleResolutionError(message)
                resolved.issues.append(message)

        resolved.files.append(
            ResolvedFile(
                declared_path=declared,
                resolved_path=str(resolved_path),
                role=str(item.get("role", "")),
                format=str(item.get("format", "")),
                required=bool(item.get("required", False)),
                exists=resolved_path.exists(),
            )
        )

    return resolved
