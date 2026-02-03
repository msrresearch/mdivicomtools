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

