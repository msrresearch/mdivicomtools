from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Any, Dict, List, Optional

try:
    from importlib.metadata import entry_points
except ImportError:  # pragma: no cover (py<3.8)
    from importlib_metadata import entry_points  # type: ignore


class PluginNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class PluginRef:
    publisher: Optional[str]
    id: str

    @classmethod
    def parse(cls, ref: str) -> "PluginRef":
        if "/" in ref:
            publisher, plugin_id = ref.split("/", 1)
            return cls(publisher=publisher or None, id=plugin_id)
        return cls(publisher=None, id=ref)


def _get_entry_points(group: str) -> List[Any]:
    eps = entry_points()
    # Python 3.10+: EntryPoints has .select(); older returns dict-like
    if hasattr(eps, "select"):
        return list(eps.select(group=group))
    return list(eps.get(group, []))


def _entry_point_locator(ep: Any) -> str:
    value = getattr(ep, "value", None)
    if value:
        return value
    module_name = getattr(ep, "module", "<module>")
    attr = getattr(ep, "attr", None)
    if attr:
        return f"{module_name}:{attr}"
    return module_name


def _normalize_plugin_contract(payload: Any, ep: Any) -> Dict[str, Any]:
    plugin: Dict[str, Any]
    if isinstance(payload, dict):
        plugin = dict(payload)
    else:
        plugin = {"value": payload}

    meta = plugin.get("meta")
    if isinstance(meta, dict):
        for key in (
            "api_version",
            "id",
            "kind",
            "version",
            "description",
            "publisher",
            "name",
            "homepage",
            "license",
            "authors",
            "inputs",
            "outputs",
            "config_schema",
        ):
            if key in meta and key not in plugin:
                plugin[key] = meta[key]

    entry = plugin.get("entry")
    if isinstance(entry, dict) and "callable" in entry and "run_ref" not in plugin:
        plugin["run_ref"] = entry["callable"]

    if not plugin.get("id"):
        plugin["id"] = getattr(ep, "name", None)
    plugin.setdefault("entry_point", _entry_point_locator(ep))
    return plugin


def _resolve_callable(callable_ref: str) -> Any:
    if ":" not in callable_ref:
        raise TypeError(f"Invalid callable reference: {callable_ref}")
    module_name, attr_path = callable_ref.split(":", 1)
    obj: Any = import_module(module_name)
    for attr in attr_path.split("."):
        obj = getattr(obj, attr)
    if not callable(obj):
        raise TypeError(f"Resolved object is not callable: {callable_ref}")
    return obj


def _ensure_python_run_callable(plugin: Dict[str, Any]) -> Dict[str, Any]:
    if callable(plugin.get("run")):
        return plugin

    run_ref = plugin.get("run_ref")
    if run_ref is None:
        entry = plugin.get("entry")
        if isinstance(entry, dict):
            run_ref = entry.get("callable")
    if not run_ref:
        return plugin

    resolved = _resolve_callable(str(run_ref))
    plugin_copy = dict(plugin)
    plugin_copy["run_ref"] = str(run_ref)
    plugin_copy["run"] = resolved
    return plugin_copy


def list_plugins() -> List[Dict[str, Any]]:
    plugins: List[Dict[str, Any]] = []
    for ep in _get_entry_points("mdivicomtools.plugins"):
        try:
            get_plugin = ep.load()
            plugin = _normalize_plugin_contract(get_plugin(), ep)
            plugins.append(plugin)
        except Exception as exc:
            plugins.append(
                {
                    "id": getattr(ep, "name", "unknown"),
                    "kind": "error",
                    "error": str(exc),
                    "entry_point": _entry_point_locator(ep),
                }
            )
    return plugins


def get_plugin(ref: PluginRef, *, resolve_execution: bool = False) -> Dict[str, Any]:
    matches: List[Dict[str, Any]] = []

    for plugin in list_plugins():
        plugin_id = plugin.get("id")
        if plugin_id != ref.id:
            continue
        if ref.publisher and plugin.get("publisher") != ref.publisher:
            continue
        matches.append(plugin)

    if not matches:
        raise PluginNotFoundError(f"Plugin not found: {ref.publisher + '/' if ref.publisher else ''}{ref.id}")
    if len(matches) > 1:
        raise PluginNotFoundError(
            f"Ambiguous plugin id '{ref.id}'. Use <publisher>/<id>. Candidates: {', '.join((p.get('publisher') or '?') + '/' + (p.get('id') or '?') for p in matches)}"
        )

    plugin = matches[0]
    if resolve_execution and plugin.get("kind", "python") == "python":
        plugin = _ensure_python_run_callable(plugin)
    return plugin
