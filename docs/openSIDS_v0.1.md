# openSIDS v0.1 (draft direction)

Goal: define a simple canonical dataset layout for multimodal social-interaction recordings that can be exported to BIDS views later (not BIDS-first).

## Canonical layout (illustrative)

```
<dataset_root>/
  dataset_manifest.yaml
  sessions/
    ses-<id>/
      ses-<id>_session.yaml
      raw/
        video/str-<id>/...
        audio/str-<id>/...
        gaze/str-<id>/...
        imu/str-<id>/...
      derived/
        sync/
          timebase_maps/<stream_id>_timebase_map.json
          sync_markers.tsv
          reports/<name>.json
        overlays/...
        transcripts/...
        annotations/...
```

## Timebase (must be explicit)

Canonical session time:
- `t_session`: seconds from session start (float; `0 = session start`).

Each stream SHOULD declare its native timebase in a sidecar:
- `raw/<stream_type>/<stream_id>/<stream_id>_stream.yaml`

## Result bundles (interop seam; minimal contract)

Result bundles are versioned, typed outputs that can be handed off safely across plugins/modules (avoid the overloaded term "artifact").

Sidecar:
- A materialized result bundle SHOULD include `resultbundle.json`.
- Preferred placement: at the payload root (adjacent to the files it describes).
- Allowed placement (read-only/vendor inputs): a detached sidecar stored under an output registry (e.g., `<out_dir>/resultbundles/.../resultbundle.json`) that points back to the payload root via `source.root`.

Minimal validation (v0.1):
- Do not require full per-type schemas yet.
- Validate only: envelope present, required files exist, required join/time keys exist.
- Unknown extra fields/columns MUST be allowed.

`resultbundle.json` required fields (v0.1):
- `resultbundle_type` (stable namespaced id; example: `pupilcloud.raw_export.v4`)
- `schema_version` (SemVer-like)
- `time_reference` (at least `kind`, `unit`)
- `files[]` (at least `path`, `role`, `format`, `required`)

Recommended fields (v0.1):
- `created_at` (UTC)
- `producer` (sidecar generator provenance; recommended keys: `tool_ref`, `tool_version`; optional `git_sha`, `pipeline_run_id`)
- `upstream_tool` (optional informational provenance of the payload generator; vendor/exporter/tool name + version)
- `source` (required when sidecar is detached): `root`, `root_base`

Key portability rule:
- Tools SHOULD NOT rewrite/rename vendor columns in-place. Instead, sidecars MAY include `files[].key_columns` mapping normalized join/time keys to the actual column names.

Point vs interval time (important for event tables):
- `files[].time.kind = point` with `key=timestamp_ns` for sample-like tables.
- `files[].time.kind = interval` with `start_key`/`end_key` for event windows (e.g. fixations, blinks).

## Sync artifacts (v0.1 proposal)

Per aligned stream (required when aligned):
- `derived/sync/timebase_maps/<stream_id>_timebase_map.json`

Session-level (recommended):
- `derived/sync/sync_markers.tsv` (the observed anchors used to estimate mappings)

## Annotations (pivot)

Use a simple events table pivot for roundtripping annotations across tools:
- `events.tsv` with `onset`/`duration` in `t_session` plus columns like `tier`, `label`, optional `person_id`, and additional attributes.

## Status

This is a draft direction. Schemas and exact filenames may evolve.
