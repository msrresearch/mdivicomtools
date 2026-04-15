from __future__ import annotations

from pathlib import Path

from mdivicomtools import plugin_registry


def test_dev_plugin_discovery_is_disabled_by_default(monkeypatch) -> None:
    monkeypatch.delenv("MDIVICOM_DEV_PLUGIN_ROOTS", raising=False)

    assert plugin_registry._get_dev_entry_points("mdivicomtools.plugins") == []


def test_list_plugins_can_load_dev_entry_points_from_opt_in_roots(
    monkeypatch, tmp_path: Path
) -> None:
    repo_root = tmp_path / "demo_plugin_repo"
    repo_root.mkdir()

    (repo_root / "pyproject.toml").write_text(
        """
[project]
name = "demo-plugin"
version = "0.1.0"

[project.entry-points."mdivicomtools.plugins"]
demo = "demo_plugin:get_plugin"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (repo_root / "demo_plugin.py").write_text(
        """
def get_plugin():
    return {
        "id": "demo",
        "kind": "python",
        "name": "Demo plugin",
    }
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(plugin_registry, "_get_entry_points", lambda group: [])
    monkeypatch.setenv("MDIVICOM_DEV_PLUGIN_ROOTS", str(repo_root))

    plugins = plugin_registry.list_plugins()

    assert len(plugins) == 1
    assert plugins[0]["id"] == "demo"
    assert plugins[0]["kind"] == "python"
    assert plugins[0]["entry_point"] == "demo_plugin:get_plugin"
