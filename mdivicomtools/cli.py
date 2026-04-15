from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .plugin_registry import PluginNotFoundError, PluginRef, get_plugin, list_plugins
from .provenance import new_run_id, run_record, write_run_record
from .resultbundles import (
    ResultBundleResolutionError,
    check_compatibility,
    get_validation_policy,
    list_validation_policies,
    parse_validation_mode,
    resolve_sidecar,
    select_validation_mode,
    validate_envelope,
)


def _json_sanitize(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for key, value in obj.items():
            if key == "run":
                continue
            out[key] = _json_sanitize(value)
        return out
    if isinstance(obj, (list, tuple)):
        return [_json_sanitize(v) for v in obj]
    if isinstance(obj, Path):
        return str(obj)
    if callable(obj):
        qualname = getattr(obj, "__qualname__", getattr(obj, "__name__", "<callable>"))
        return f"{getattr(obj, '__module__', '<module>')}:{qualname}"
    return obj


def _parse_config(config_arg: Optional[str]) -> Dict[str, Any]:
    if not config_arg:
        return {}

    candidate_path = Path(config_arg)
    if candidate_path.exists():
        return json.loads(candidate_path.read_text(encoding="utf-8"))

    return json.loads(config_arg)


def _parse_optional_dir(path_arg: Optional[str]) -> Optional[Path]:
    if not path_arg:
        return None
    return Path(path_arg).expanduser().resolve(strict=False)


def _resolve_sidecar_from_args(args: argparse.Namespace, *, strict: bool) -> Any:
    return resolve_sidecar(
        args.sidecar,
        dataset_dir=_parse_optional_dir(args.dataset_dir),
        out_dir=_parse_optional_dir(args.out_dir),
        cwd=_parse_optional_dir(args.cwd),
        strict=strict,
    )


def _cmd_plugins_list(args: argparse.Namespace) -> int:
    plugins = list_plugins()
    if args.json:
        print(json.dumps(_json_sanitize(plugins), indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    if not plugins:
        print("(no plugins found)")
        return 0

    for plugin in plugins:
        publisher = plugin.get("publisher")
        plugin_id = plugin.get("id") or "unknown"
        kind = plugin.get("kind") or "unknown"
        version = plugin.get("version") or "unknown"
        prefix = f"{publisher}/" if publisher else ""
        print(f"{prefix}{plugin_id}\t{kind}\t{version}")
    return 0


def _cmd_plugins_info(args: argparse.Namespace) -> int:
    plugin_ref = PluginRef.parse(args.plugin_ref)
    plugin = get_plugin(plugin_ref)
    print(json.dumps(_json_sanitize(plugin), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    plugin_ref = PluginRef.parse(args.plugin_ref)
    plugin = get_plugin(plugin_ref, resolve_execution=True)

    dataset_dir = Path(args.dataset).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve()
    work_dir = Path(args.work).expanduser().resolve() if args.work else None
    config = _parse_config(args.config)

    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = new_run_id()
    record_path = write_run_record(out_dir, run_id, run_record(plugin=plugin, dataset_dir=dataset_dir, out_dir=out_dir, work_dir=work_dir, config=config, backend=args.backend))

    try:
        backend = args.backend
        if backend == "auto":
            backend = plugin.get("kind", "python")

        if backend == "python":
            run_fn = plugin.get("run")
            if not callable(run_fn):
                raise TypeError(f"Plugin {plugin.get('id')} is missing a callable 'run' function")
            run_fn(dataset_dir=dataset_dir, out_dir=out_dir, config=config, work_dir=work_dir, dry_run=bool(args.dry_run))
        elif backend == "docker":
            raise NotImplementedError("docker backend is not implemented in this scaffold yet")
        else:
            raise ValueError(f"Unknown backend: {backend}")

        return 0
    except Exception as exc:
        raise SystemExit(f"Run failed (run_id={run_id}). See {record_path} for provenance. Error: {exc}") from exc


def _cmd_resultbundles_inspect(args: argparse.Namespace) -> int:
    try:
        resolved = _resolve_sidecar_from_args(args, strict=False)
    except ResultBundleResolutionError as exc:
        raise SystemExit(str(exc)) from exc
    payload = resolved.to_dict()

    if args.json:
        print(json.dumps(_json_sanitize(payload), indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    print(f"sidecar: {payload['sidecar_path']}")
    print(f"payload_root: {payload['payload_root']}")
    print(f"detached: {payload['detached']}")
    print(f"type: {payload.get('resultbundle_type')}")
    print(f"schema_version: {payload.get('schema_version')}")

    files = payload.get("files", [])
    if not files:
        print("files: (none)")
    for item in files:
        status = "ok" if item.get("exists") else "missing"
        requirement = "required" if item.get("required") else "optional"
        print(f"file: {item.get('declared_path')} ({requirement}, {status}) -> {item.get('resolved_path')}")

    for warning in payload.get("warnings", []):
        print(f"warning: {warning}")
    for issue in payload.get("issues", []):
        print(f"issue: {issue}")
    return 0


def _cmd_resultbundles_validate(args: argparse.Namespace) -> int:
    selected_policy = None
    if args.policy:
        selected_policy = get_validation_policy(args.policy)

    mode = parse_validation_mode(
        select_validation_mode(
            mode=args.mode,
            policy=args.policy,
            default_mode="strict",
        )
    )
    hard_fail = False
    compatibility = None

    try:
        resolved = _resolve_sidecar_from_args(args, strict=(mode == "strict"))
    except ResultBundleResolutionError as exc:
        report = {"mode": mode, "valid": False, "errors": [str(exc)], "warnings": [], "notes": []}
        if args.json:
            print(json.dumps({"validation": report}, indent=2, ensure_ascii=False, sort_keys=True))
        else:
            print(f"validation: invalid (mode={mode})")
            print(f"error: {exc}")
        return 1

    report = validate_envelope(resolved.sidecar, mode=mode, resolved=resolved)

    perform_compat_check = args.expect_type is not None or args.supported_major is not None or args.min_minor is not None
    if perform_compat_check:
        expected_type = args.expect_type or str(resolved.sidecar.get("resultbundle_type") or "")
        if not expected_type:
            message = "Compatibility check requested but sidecar has no resultbundle_type and no --expect-type was provided."
            if mode == "strict":
                report.add_error(message)
                hard_fail = True
            else:
                report.add_warning(message)
        else:
            compatibility = check_compatibility(
                resolved.sidecar,
                expected_type=expected_type,
                supported_major=args.supported_major,
                min_minor=args.min_minor,
            )
            if not compatibility.compatible:
                if mode == "strict":
                    report.add_error(compatibility.reason)
                    hard_fail = True
                else:
                    report.add_warning(compatibility.reason)
            elif compatibility.level == "warn":
                report.add_warning(compatibility.reason)
            else:
                report.add_note(compatibility.reason)

    payload: Dict[str, Any] = {
        "resolved": resolved.to_dict(),
        "validation": report.to_dict(),
    }
    if selected_policy is not None:
        payload["policy"] = selected_policy.to_dict()
    if compatibility is not None:
        payload["compatibility"] = compatibility.to_dict()

    if args.json:
        print(json.dumps(_json_sanitize(payload), indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(f"validation: {'valid' if report.valid and not hard_fail else 'invalid'} (mode={mode})")
        if selected_policy is not None:
            print(f"policy: {selected_policy.name} (fallback_allowed={selected_policy.allow_fallback})")
        for err in report.errors:
            print(f"error: {err}")
        for warning in report.warnings:
            print(f"warning: {warning}")
        for note in report.notes:
            print(f"note: {note}")
        if compatibility is not None:
            status = "compatible" if compatibility.compatible else "incompatible"
            print(f"compatibility: {status} ({compatibility.level}) - {compatibility.reason}")

    if not report.valid or hard_fail:
        return 1
    return 0


def _cmd_resultbundles_policies(args: argparse.Namespace) -> int:
    policies = {name: policy.to_dict() for name, policy in sorted(list_validation_policies().items())}
    if args.json:
        print(json.dumps(_json_sanitize({"policies": policies}), indent=2, ensure_ascii=False, sort_keys=True))
        return 0

    for name, policy in policies.items():
        print(
            f"{name}\tmode={policy['validation_mode']}\t"
            f"fallback={policy['allow_fallback']}\t"
            f"fallback_reason={policy['require_fallback_reason']}"
        )
        print(f"  {policy['description']}")
    return 0


def _add_resultbundle_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--sidecar", required=True, help="Path to resultbundle.json sidecar")
    parser.add_argument("--dataset-dir", help="Dataset root used when source.root_base=dataset_dir")
    parser.add_argument("--out-dir", help="Output root used when source.root_base=out_dir")
    parser.add_argument("--cwd", help="Fallback base used when source.root_base=cwd")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mdivicom")
    sub = parser.add_subparsers(dest="cmd", required=True)

    plugins = sub.add_parser("plugins", help="List or inspect available plugins")
    plugins_sub = plugins.add_subparsers(dest="plugins_cmd", required=True)

    plugins_list = plugins_sub.add_parser("list", help="List installed plugins")
    plugins_list.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    plugins_list.set_defaults(_handler=_cmd_plugins_list)

    plugins_info = plugins_sub.add_parser("info", help="Show plugin metadata")
    plugins_info.add_argument("plugin_ref", help="Plugin reference (<id> or <publisher>/<id>)")
    plugins_info.set_defaults(_handler=_cmd_plugins_info)

    run = sub.add_parser("run", help="Run a plugin (scaffold)")
    run.add_argument("plugin_ref", help="Plugin reference (<id> or <publisher>/<id>)")
    run.add_argument("--dataset", required=True, help="Dataset/input directory")
    run.add_argument("--out", required=True, help="Output directory (run root)")
    run.add_argument("--work", help="Optional working directory")
    run.add_argument("--config", help="Config JSON or path to JSON file")
    run.add_argument("--backend", choices=["auto", "python", "docker"], default="auto")
    run.add_argument("--dry-run", action="store_true")
    run.set_defaults(_handler=_cmd_run)

    resultbundles = sub.add_parser("resultbundles", help="Inspect and validate resultbundle sidecars")
    resultbundles_sub = resultbundles.add_subparsers(dest="resultbundles_cmd", required=True)

    resultbundles_inspect = resultbundles_sub.add_parser("inspect", help="Resolve and inspect a resultbundle sidecar")
    _add_resultbundle_common_args(resultbundles_inspect)
    resultbundles_inspect.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    resultbundles_inspect.set_defaults(_handler=_cmd_resultbundles_inspect)

    resultbundles_policies = resultbundles_sub.add_parser(
        "policies", help="List standard validation policy profiles for local/plugin pipelines"
    )
    resultbundles_policies.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    resultbundles_policies.set_defaults(_handler=_cmd_resultbundles_policies)

    resultbundles_validate = resultbundles_sub.add_parser("validate", help="Validate resultbundle envelope and compatibility")
    _add_resultbundle_common_args(resultbundles_validate)
    resultbundles_validate.add_argument("--mode", choices=["strict", "warn", "off"], default=None)
    resultbundles_validate.add_argument(
        "--policy",
        choices=sorted(list_validation_policies()),
        help="Optional policy preset that supplies a default validation mode and fallback expectations",
    )
    resultbundles_validate.add_argument("--expect-type", help="Expected resultbundle_type")
    resultbundles_validate.add_argument("--supported-major", type=int, help="Supported schema major version")
    resultbundles_validate.add_argument("--min-minor", type=int, help="Preferred minimum schema minor version")
    resultbundles_validate.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    resultbundles_validate.set_defaults(_handler=_cmd_resultbundles_validate)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        handler = args._handler
    except AttributeError as exc:  # pragma: no cover
        raise SystemExit(f"Internal error: no handler for command {args}") from exc

    try:
        return int(handler(args))
    except PluginNotFoundError as exc:
        raise SystemExit(str(exc)) from exc
