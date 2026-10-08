"""CLI writes must preserve input trees even when a plugin would reject later."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from mdivicomtools import cli


def _dataset(root):
    dataset = root / "input"
    (dataset / "nested").mkdir(parents=True)
    (dataset / "signal.bin").write_bytes(b"\x00\x01\x02")
    (dataset / "nested" / "events.tsv").write_text("onset\tduration\n0\t1\n", encoding="utf-8")
    return dataset


def _tree(root):
    result = {}
    for path in root.rglob("*"):
        name = str(path.relative_to(root))
        if path.is_symlink():
            result[name] = ("symlink", os.readlink(path))
        elif path.is_dir():
            result[name] = ("directory",)
        else:
            result[name] = ("file", path.read_bytes())
    return result


def _rejecting_plugin(monkeypatch):
    calls = []
    def run(**kwargs):
        raise AssertionError("Rejected paths reached plugin execution")
    def load(*args, **kwargs):
        calls.append((args, kwargs))
        return {"id": "demo", "kind": "python", "version": "0.1.0", "run": run}
    monkeypatch.setattr(cli, "get_plugin", load)
    return calls


def _assert_rejected(monkeypatch, root, dataset, out, work, dry_run):
    calls = _rejecting_plugin(monkeypatch)
    args = ["run", "demo", "--dataset", str(dataset), "--out", str(out)]
    if work is not None:
        args.extend(["--work", str(work)])
    if dry_run:
        args.append("--dry-run")
    before = _tree(root)
    with pytest.raises(SystemExit, match="must be disjoint from --dataset"):
        cli.main(args)
    assert _tree(root) == before
    assert calls == []  # no plugin loading, execution, output mkdir or run record


@pytest.mark.parametrize("option", ["out", "work"])
@pytest.mark.parametrize("relation", ["equal", "parent", "child"])
@pytest.mark.parametrize("dry_run", [False, True])
def test_overlap_rejection_preserves_full_tree(tmp_path, monkeypatch, option, relation, dry_run):
    dataset = _dataset(tmp_path)
    target = {"equal": dataset, "parent": dataset.parent, "child": dataset / "new" / "output"}[relation]
    out = target if option == "out" else tmp_path / "separate-output"
    work = target if option == "work" else None
    _assert_rejected(monkeypatch, tmp_path, dataset, out, work, dry_run)


@pytest.mark.parametrize("option", ["out", "work"])
@pytest.mark.parametrize("relation", ["equal", "parent", "child"])
def test_symlink_alias_cannot_bypass_overlap_rejection(tmp_path, monkeypatch, option, relation):
    dataset = _dataset(tmp_path)
    target = {"equal": dataset, "parent": dataset.parent, "child": dataset / "nested"}[relation]
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(target, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Directory symlinks unavailable: {exc}")
    out = alias if option == "out" else tmp_path / "separate-output"
    work = alias if option == "work" else None
    _assert_rejected(monkeypatch, tmp_path, dataset, out, work, True)


def test_dataset_symlink_is_resolved_before_overlap_check(tmp_path, monkeypatch):
    dataset = _dataset(tmp_path)
    alias = tmp_path / "input-alias"
    try:
        alias.symlink_to(dataset, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"Directory symlinks unavailable: {exc}")
    _assert_rejected(monkeypatch, tmp_path, alias, dataset / "new-output", None, False)


@pytest.mark.parametrize("dry_run", [False, True])
def test_isolated_run_retains_arguments_and_run_record_behavior(tmp_path, monkeypatch, dry_run):
    dataset = _dataset(tmp_path)
    out = tmp_path / "input-output"  # shared name prefix is not path overlap
    work = tmp_path / "input-work"
    calls = []
    def run(**kwargs):
        calls.append(kwargs)
        if not kwargs["dry_run"]:
            (kwargs["out_dir"] / "payload.txt").write_text("synthetic", encoding="utf-8")
            kwargs["work_dir"].mkdir()
            (kwargs["work_dir"] / "scratch.txt").write_text("work", encoding="utf-8")
    monkeypatch.setattr(cli, "get_plugin", lambda *a, **k: {"id": "demo", "kind": "python", "version": "0.1.0", "run": run})
    before = _tree(dataset)
    args = ["run", "demo", "--dataset", str(dataset), "--out", str(out), "--work", str(work), "--config", '{"setting": false}']
    if dry_run:
        args.append("--dry-run")
    assert cli.main(args) == 0
    assert _tree(dataset) == before
    assert calls == [{"dataset_dir": dataset.resolve(), "out_dir": out.resolve(), "work_dir": work.resolve(), "config": {"setting": False}, "dry_run": dry_run}]
    records = list((out / "_runs").glob("*.json"))
    assert len(records) == 1
    record = json.loads(records[0].read_text(encoding="utf-8"))
    assert record["dataset_dir"] == str(dataset.resolve())
    assert record["out_dir"] == str(out.resolve()) and record["work_dir"] == str(work.resolve())
    assert record["plugin"]["id"] == "demo" and record["backend"] == "auto"
    assert (out / "payload.txt").exists() is (not dry_run)


@pytest.mark.parametrize("alias_kind", ["case", "unicode", "firmlink"])
@pytest.mark.parametrize("option", ["out", "work"])
@pytest.mark.parametrize("relation", ["equal", "parent", "child"])
def test_filesystem_alias_cannot_bypass_overlap_rejection(tmp_path, monkeypatch, alias_kind, option, relation):
    parent, alias = _aliased_parent(tmp_path, alias_kind)
    dataset = _dataset(parent)
    target = {"equal": alias / "input", "parent": alias, "child": alias / "input" / "new"}[relation]
    out = target if option == "out" else tmp_path / "separate-output"
    work = target if option == "work" else None
    _assert_rejected(monkeypatch, tmp_path, dataset, out, work, True)


def _aliased_parent(root, kind):
    parent = root / ("café" if kind == "unicode" else "Parent")
    parent.mkdir()
    if kind == "case":
        alias = parent.with_name("PARENT")
    elif kind == "unicode":
        alias = parent.with_name("cafe\u0301")
    else:
        alias = Path("/System/Volumes/Data") / parent.relative_to(parent.anchor)
    if not alias.exists() or not alias.samefile(parent):
        pytest.skip(f"{kind} filesystem alias unavailable on this volume")
    return parent, alias


@pytest.mark.parametrize("alias_kind", ["case", "unicode", "firmlink"])
def test_isolated_siblings_under_an_aliased_parent_are_allowed(tmp_path, monkeypatch, alias_kind):
    parent, alias = _aliased_parent(tmp_path, alias_kind)
    dataset = _dataset(parent)
    calls = []
    monkeypatch.setattr(cli, "get_plugin", lambda *a, **k: {
        "id": "demo", "kind": "python", "run": lambda **kwargs: calls.append(kwargs)
    })
    before = _tree(dataset)
    out = alias / "separate-output"
    assert cli.main(["run", "demo", "--dataset", str(dataset), "--out", str(out),
                     "--work", str(alias / "separate-work"), "--dry-run"]) == 0
    assert len(calls) == 1 and _tree(dataset) == before
    assert len(list((out / "_runs").glob("*.json"))) == 1
