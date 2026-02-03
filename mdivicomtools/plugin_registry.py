from __future__ import annotations

from dataclasses import dataclass
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


def list_plugins() -> List[Dict[str, Any]]:
    plugins: List[Dict[str, Any]] = []
    for ep in _get_entry_points("mdivicomtools.plugins"):
        try:
            get_plugin = ep.load()
            plugin = get_plugin()
            plugin = dict(plugin) if isinstance(plugin, dict) else {"value": plugin}
            plugin.setdefault("id", getattr(ep, "name", None))
            plugin.setdefault("entry_point", getattr(ep, "value", None) or f"{ep.module}:{ep.attr}")
            plugins.append(plugin)
        except Exception as exc:
            plugins.append(
                {
                    "id": getattr(ep, "name", "unknown"),
                    "kind": "error",
                    "error": str(exc),
                    "entry_point": getattr(ep, "value", None) or f"{ep.module}:{ep.attr}",
                }
            )
    return plugins


def get_plugin(ref: PluginRef) -> Dict[str, Any]:
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
    return matches[0]
