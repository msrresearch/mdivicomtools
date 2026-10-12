# Resultbundle Runtime Integration v0.1

Status:
- draft
- public runtime seam version: `v0.1`

This note integrates the follow-up handoff requests in the central
resultbundle thread and documents the current core stance for plugin authors.

## What Is Stable Now

Core runtime surface in `mdivicomtools.resultbundles`:

- `resolve_sidecar(...)`
- `validate_envelope(...)`
- `check_compatibility(...)`
- validation policy profiles:
  - `local_default`
  - `plugin_strict`
  - `pipeline_auto`
  - `legacy_off`

Normalization/compatibility behavior (v0.1):
- Canonical write-new vendor/export provenance key: `upstream_tool`
  - Readers accept legacy aliases (`payload_provenance`, `upstream`) and normalize to `upstream_tool`.
- Canonical detached sidecar base vocabulary: `source.root_base in {dataset_dir, out_dir}` (portable)
  - Readers accept legacy aliases (`input_data_dir`, `output_data_dir`) and normalize to the canonical values.
  - Non-portable values like `absolute` are permitted for local/dev but should warn/fail in strict external handoff validation.

CLI surface:

- `mdivicom resultbundles inspect ...`
- `mdivicom resultbundles validate ...`
- `mdivicom resultbundles policies [--json]`

## Minimum envelope and exact validation scope

Required envelope keys are `resultbundle_type` and `schema_version` (non-empty
strings), `time_reference` (object with non-empty `kind` and `unit` strings), and
`files` (non-empty array). Each file entry requires `path`, `role` and `format`
(non-empty strings) plus `required` (boolean). Null placeholders do not satisfy
these fields. Unknown extra fields remain allowed.

`files[].sha256` is optional. When declared, it must be exactly 64 ASCII hexadecimal
characters, with either letter case accepted. With resolved payloads, validation
streams the actual enclosed regular file and compares its SHA-256. A malformed
hash, mismatch or unreadable/non-regular present payload is an error in `strict`
and a warning in `warn`. Files outside the payload root and files under a root
that violates its declared base are not read for hashing, even in `warn` or after
non-strict resolution followed by strict validation. An absent optional file
remains permitted and, when a hash is declared, is noted as unverified; missing
required files fail strict validation. Hash-free bundles
retain their existing behavior. `off` skips envelope and integrity checks.

The CLI still loads/resolves the sidecar in every mode. `inspect` and
`resolve_sidecar(...)` alone do not verify content hashes. Python callers should
pass `resolved` to `validate_envelope(resolved.sidecar, resolved=resolved)`;
envelope-only calls check structure/hash syntax and note that payload hashes
were not verified. Structural envelope errors remain errors in `warn`.

With resolved data, strict validation covers envelope/file structure, relative
payload containment, portable detached roots, required-file presence and declared
hash integrity. Type/version compatibility is a separate API check, or is added
by CLI compatibility flags. Validation does not parse tables, verify time/join
keys, interpret domain types, establish scientific validity or authenticate the
producer. Hashes check declared bytes, not those semantic properties. Only declared
entries are examined; undeclared extra files are ignored. Hash-free required entries
receive existence checks, not regular-file checks.

## Recommended Integration Seam

Primary seam for non-Python or R pipelines:

- Use the CLI with `--json` output.
- Treat CLI JSON as the contract boundary for wrappers.

Primary seam for Python-native plugins:

- Use `mdivicomtools.resultbundles` API directly.

Rationale:

- CLI-first wrapper integration keeps runtime dependencies isolated for R repos.
- API access stays available for in-process Python plugins and tests.

## Operating Model (Local vs Plugin/Pipeline)

Use one of the policy profiles below:

| Profile | Validation Mode | Fallback Allowed | Intended Use |
| --- | --- | --- | --- |
| `local_default` | `off` | yes | Local CSV-first workflows; no strict external handoff guarantees |
| `plugin_strict` | `strict` | no | External plugin-to-plugin handoff; fail fast on incompatibility |
| `pipeline_auto` | `warn` | yes (reason required) | Transitional automation path; fallback allowed with persisted reason |
| `legacy_off` | `off` | yes | Legacy compatibility or controlled internal recompute paths |

External handoff recommendation:

- Start in `plugin_strict`.
- If migration pressure exists, temporarily use `pipeline_auto`.
- Record explicit fallback reasons in the caller's run/provenance logs.

## Migration Guidance (Plugin Repos, Including R-First Repos)

1. Keep existing bundle emission but stop duplicating generic resolver/validator logic.
2. Add a small wrapper around one CLI call:
   - `mdivicom resultbundles validate --json --policy plugin_strict ...`
3. Parse JSON output in the wrapper and route to:
   - hard fail (`plugin_strict`), or
   - controlled fallback (`pipeline_auto`) with persisted fallback reason.
4. Keep plugin-specific semantic checks local (for example timeline coverage or
   domain-specific column rules).
5. Remove bespoke duplicated bundle envelope/type/version checks after parity.

## Deferred (Not v0.1 Core)

- Per-type join/time-key validation beyond the shared envelope and compatibility checks.
- Full per-type JSON Schema bundles.
- Automatic major-version adapters.
- Central registry service/discovery beyond local contracts.
