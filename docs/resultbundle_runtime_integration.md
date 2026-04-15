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
