# Plugin contract v0.1 (draft)

Goal: enable a two-lane plugin ecosystem that supports both lightweight Python plugins and dependency-isolated container/tool plugins.

v0.1 priorities:
- stable discovery
- a minimal run contract (dataset in, outputs out, config in)
- output isolation (plugins must not collide)

Non-goals (v0.1):
- full workflow DSL
- strict openSIDS schema enforcement everywhere (start with minimal seams)

## Two-lane model

- Lane A: `kind=python` (in-process; lightweight dependencies)
- Lane B: `kind=container` (isolated runtime; docker now, other backends later)

## Discovery

Python plugins register entry points under:
- group: `mdivicomtools.plugins`

Each entry point resolves to a callable:
- `get_plugin() -> dict`

v0.1 rule: keep plugin registration JSON-safe so the CLI can list/info plugins without importing heavy dependencies.

Recommended return shape:

```json
{
  "meta": {
    "api_version": "mdivicomtools.plugin.v0.1",
    "id": "sync-audio",
    "kind": "python",
    "version": "0.1.0",
    "description": "Sync multi-camera audio/video streams."
  },
  "entry": {
    "callable": "mditools_sync_audio.run:run"
  }
}
```

## Plugin metadata (minimum)

Plugins MUST return `meta` with:
- `api_version` (v0.1: `mdivicomtools.plugin.v0.1`)
- `id` (short slug, unique in an environment)
- `kind` (`python` or `container`)
- `version` (SemVer recommended)
- `description`

Recommended:
- `publisher` (org/user name; enables `<publisher>/<id>` namespacing)

## Execution contract (python lane)

Python plugins provide:
- `run(dataset_dir, out_dir, config, *, work_dir=None, dry_run=False) -> None`

Conventions:
- `dataset_dir` is treated as read-only.
- `out_dir` is the plugin-scoped output root (`plugin_out_dir`).
  - The runner is responsible for output isolation by construction (e.g., `plugin_out_dir = <run_out_dir>/<plugin_id>`).
- Dataset-producing plugins SHOULD write an openSIDS dataset view under: `<out_dir>/dataset/**`.
- Plugins SHOULD write a plugin-level provenance record under: `<out_dir>/provenance.json`.

## Execution contract (container/tool lane)

Container/tool plugins provide a manifest describing:
- image, command argv, and mount conventions

Runner expectations (v0.1):
- dataset mounted read-only
- outputs mounted read-write
- optional work dir mounted read-write
- runner captures run-level provenance (plugin id/version, backend, config hash, timestamps, exit status; plus container image tag/digest when available)

## Result bundles (interop seam)

If outputs are intended for cross-plugin handoff, producers SHOULD emit `resultbundle.json` sidecars describing typed result bundles (type id + schema_version + file inventory + join/time key mapping).

See:
- `docs/openSIDS_v0.1.md` (Result bundles section)

## CLI surface (scaffold)

The public core aims to provide:
- `mdivicom plugins list`
- `mdivicom plugins info <plugin_ref>`
- `mdivicom run <plugin_ref> --dataset ... --out ...`

## Status

Draft spec. Keep it minimal and stable for v0.1.
