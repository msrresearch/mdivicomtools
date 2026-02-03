# Plugin contract v0.1 (draft)

Goal: enable a two-lane plugin ecosystem that supports both lightweight Python plugins and dependency-isolated docker/tool plugins.

## Discovery

Python plugins register entry points under:
- group: `mdivicomtools.plugins`

Each entry point resolves to a callable:
- `get_plugin() -> dict`

## Plugin metadata (minimum)

Plugins return a dict with at least:
- `id` (short slug, unique in an environment)
- `kind` (`python` or `docker`)
- `version`
- `description`

Recommended:
- `publisher` (org/user name; enables `<publisher>/<id>` namespacing)

## Execution (python lane)

Python plugins provide a callable `run(...)`:
- `run(dataset_dir, out_dir, config, *, work_dir=None, dry_run=False) -> None`

Conventions:
- outputs should be written under `<out_dir>/<plugin_id>/...`
- dataset-producing plugins should write a dataset under `<out_dir>/<plugin_id>/dataset/**`

## Execution (docker/tool lane)

Docker/tool plugins provide a manifest describing:
- image / command / mounts

The runner executes the container with stable mounts:
- dataset in (read-only)
- outputs out
- optional work dir

## CLI surface (scaffold)

The public core aims to provide:
- `mdivicom plugins list`
- `mdivicom plugins info <plugin_ref>`
- `mdivicom run <plugin_ref> --dataset ... --out ...`

## Status

Draft spec. Keep it minimal and stable for v0.1.

