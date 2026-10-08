"""Declared integrity is checked on the actual resolved payload, through API and CLI."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from mdivicomtools import cli
from mdivicomtools.resultbundles import resolve_sidecar, validate_envelope
from test_resultbundles import _write_json


ABC_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def _bundle(root, detached=False, required=True):
    out = root / "output"
    payload = out / "payload" / "payload.txt"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"abc")
    sidecar = {
        "resultbundle_type": "example.text", "schema_version": "0.1.0",
        "time_reference": {"kind": "sample", "unit": "index"},
        "files": [{"path": "payload.txt", "role": "data", "format": "text/plain", "required": required, "sha256": ABC_SHA256}],
    }
    path = out / "sidecars" / "resultbundle.json" if detached else payload.parent / "resultbundle.json"
    if detached:
        sidecar["source"] = {"root": "payload", "root_base": "out_dir"}
    _write_json(path, sidecar)
    return path, out, payload, sidecar


def _validate(path, out, mode="strict"):
    resolved = resolve_sidecar(path, out_dir=out, strict=(mode == "strict"))
    return validate_envelope(resolved.sidecar, resolved=resolved, mode=mode)


@pytest.mark.parametrize("detached", [False, True])
def test_attached_and_detached_hashes_verify_current_bytes(tmp_path, detached):
    path, out, payload, sidecar = _bundle(tmp_path, detached)
    sidecar["files"][0]["sha256"] = ABC_SHA256.upper()
    _write_json(path, sidecar)
    report = _validate(path, out)
    assert report.valid and not report.errors
    assert any("Verified SHA-256" in note for note in report.notes)


@pytest.mark.parametrize("detached", [False, True])
@pytest.mark.parametrize("mode", ["strict", "warn", "off"])
def test_tampering_has_mode_specific_api_and_cli_results(tmp_path, capsys, detached, mode):
    path, out, payload, sidecar = _bundle(tmp_path, detached)
    payload.write_bytes(b"def")
    before = {p: p.read_bytes() for p in out.rglob("*") if p.is_file()}
    report = _validate(path, out, mode)
    assert report.valid is (mode != "strict")
    if mode != "off":
        assert any("SHA-256 mismatch" in message for message in report.errors + report.warnings)
    else:
        assert not report.errors and not report.warnings
    code = cli.main(["resultbundles", "validate", "--sidecar", str(path), "--out-dir", str(out), "--mode", mode, "--json"])
    output = json.loads(capsys.readouterr().out)
    assert code == (1 if mode == "strict" else 0)
    assert output["validation"]["valid"] is report.valid
    assert {p: p.read_bytes() for p in out.rglob("*") if p.is_file()} == before


@pytest.mark.parametrize("expected", [None, 42, True, "", "0" * 63, "0" * 65, "g" * 64, "f" * 63 + "\n", "Ｆ" * 64])
@pytest.mark.parametrize("mode", ["strict", "warn"])
def test_malformed_declared_hash_is_not_treated_as_absent(tmp_path, expected, mode):
    path, out, payload, sidecar = _bundle(tmp_path)
    sidecar["files"][0]["sha256"] = expected
    _write_json(path, sidecar)
    report = _validate(path, out, mode)
    assert report.valid is (mode == "warn")
    assert any("sha256 must be exactly 64" in message for message in report.errors + report.warnings)


@pytest.mark.parametrize("required", [False, True])
@pytest.mark.parametrize("mode", ["strict", "warn"])
def test_missing_optional_and_required_hashed_payloads(tmp_path, required, mode):
    path, out, payload, sidecar = _bundle(tmp_path, required=required)
    payload.unlink()
    report = _validate(path, out, mode)
    assert report.valid is (not required or mode == "warn")
    if not required:
        assert any("Optional payload absent" in note and "not verified" in note for note in report.notes)
    else:
        assert report.errors or report.warnings


def test_hash_free_bundle_compatibility_is_preserved(tmp_path):
    path, out, payload, sidecar = _bundle(tmp_path)
    del sidecar["files"][0]["sha256"]
    _write_json(path, sidecar)
    payload.write_bytes(b"unhashed content")
    report = _validate(path, out)
    assert report.valid and not report.errors and not report.warnings
    assert not report.notes


def test_rebinding_detached_bundle_checks_actual_resolved_root(tmp_path):
    path, out, payload, sidecar = _bundle(tmp_path, detached=True)
    other = tmp_path / "other-output"
    (other / "payload").mkdir(parents=True)
    (other / "payload" / "payload.txt").write_bytes(b"other content")
    report = _validate(path, other)
    assert not report.valid and any("SHA-256 mismatch" in error for error in report.errors)
    (other / "payload" / "payload.txt").write_bytes(b"abc")
    assert _validate(path, other).valid  # actual bytes, not sidecar location, decide integrity
    assert _validate(path, out).valid


def test_envelope_only_call_reports_unverified_payload_hash(tmp_path):
    path, out, payload, sidecar = _bundle(tmp_path)
    payload.write_bytes(b"not examined by envelope-only call")
    report = validate_envelope(sidecar)
    assert report.valid and any("not verified without resolved" in note for note in report.notes)
    assert not _validate(path, out).valid


def test_warn_mode_does_not_read_a_payload_escape(tmp_path, monkeypatch):
    path, out, payload, sidecar = _bundle(tmp_path)
    outside = out / "outside.txt"; outside.write_bytes(b"abc")
    sidecar["files"][0]["path"] = "../outside.txt"
    _write_json(path, sidecar)
    resolved = resolve_sidecar(path, strict=False)
    opened = []
    def forbidden_read(*args, **kwargs):
        opened.append(args)
        raise AssertionError("Hash validation read outside payload root")
    monkeypatch.setattr(Path, "open", forbidden_read)
    report = validate_envelope(resolved.sidecar, resolved=resolved, mode="warn")
    assert report.valid and not opened
    assert any("SHA-256 not verified outside" in warning for warning in report.warnings)


@pytest.mark.parametrize("mode", ["strict", "warn"])
def test_hash_read_error_becomes_a_validation_issue(tmp_path, monkeypatch, mode):
    path, out, payload, sidecar = _bundle(tmp_path)
    resolved = resolve_sidecar(path)
    def denied(*args, **kwargs):
        raise PermissionError("synthetic read denial")
    monkeypatch.setattr(Path, "open", denied)
    report = validate_envelope(resolved.sidecar, resolved=resolved, mode=mode)
    assert report.valid is (mode == "warn")
    assert any("PermissionError" in message for message in report.errors + report.warnings)


def test_optional_file_stat_error_is_not_reported_as_absence(tmp_path, monkeypatch):
    path, out, payload, sidecar = _bundle(tmp_path, required=False)
    resolved = resolve_sidecar(path)
    original = Path.stat
    def denied(self, *args, **kwargs):
        if self == payload:
            raise PermissionError("synthetic stat denial")
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "stat", denied)
    report = validate_envelope(resolved.sidecar, resolved=resolved)
    assert not report.valid and any("PermissionError" in error for error in report.errors)
    assert not any("Optional payload absent" in note for note in report.notes)


@pytest.mark.parametrize("kind", ["directory", "fifo"])
def test_hashing_requires_a_regular_file(tmp_path, monkeypatch, kind):
    path, out, payload, sidecar = _bundle(tmp_path)
    payload.unlink()
    if kind == "directory":
        payload.mkdir()
    else:
        if not hasattr(os, "mkfifo"):
            pytest.skip("FIFO unavailable on this platform")
        os.mkfifo(payload)
    original = Path.open
    def never_open_nonregular(self, *args, **kwargs):
        assert self != payload, "Non-regular payload must not be opened"
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "open", never_open_nonregular)
    report = _validate(path, out)
    assert not report.valid and any("regular payload file" in error for error in report.errors)


def test_hash_covers_content_beyond_one_read_chunk(tmp_path):
    path, out, payload, sidecar = _bundle(tmp_path)
    content = b"a" * (1024 * 1024) + b"tail"
    payload.write_bytes(content)
    sidecar["files"][0]["sha256"] = hashlib.sha256(content).hexdigest()
    _write_json(path, sidecar)
    assert _validate(path, out).valid
    with payload.open("ab") as stream:
        stream.write(b"tamper")
    assert not _validate(path, out).valid


@pytest.mark.parametrize("bad_index", [0, 1])
def test_every_duplicate_inventory_declaration_is_checked(tmp_path, bad_index):
    path, out, payload, sidecar = _bundle(tmp_path)
    sidecar["files"].append(dict(sidecar["files"][0]))
    sidecar["files"][bad_index]["sha256"] = "0" * 64
    _write_json(path, sidecar)
    assert not _validate(path, out).valid


@pytest.mark.parametrize("field", ["resultbundle_type", "schema_version", "path", "role", "format", "required"])
@pytest.mark.parametrize("mode", ["strict", "warn"])
def test_required_envelope_fields_cannot_use_null_placeholders(tmp_path, field, mode):
    path, out, payload, sidecar = _bundle(tmp_path)
    if field in {"resultbundle_type", "schema_version"}:
        sidecar[field] = None
    else:
        sidecar["files"][0][field] = None
    report = validate_envelope(sidecar, mode=mode)
    assert not report.valid and report.errors  # structure errors stay fatal in warn mode
