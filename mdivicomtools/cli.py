from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .plugin_registry import PluginNotFoundError, PluginRef, get_plugin, list_plugins
from .provenance import new_run_id, run_record, write_run_record


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
    plugin = get_plugin(plugin_ref)

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
