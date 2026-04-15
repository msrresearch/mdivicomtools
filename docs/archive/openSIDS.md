# openSIDS (archived public draft summary)

Status:
- archived public draft
- public document version: `v0.1`

This page is the public summary of the current openSIDS direction: a canonical dataset model for multimodal social-interaction recordings that can later be exported into BIDS-like views. The design is intentionally openSIDS-first rather than BIDS-first.

## Current contract at a glance

- The canonical prepared-data unit is one **session** (`ses-*`)
- A session is one **sync domain**
- Canonical time is `t_session` in seconds from the declared session start
- The public annotation pivot is `events.tsv` plus optional `events.json`
- Consumer-specific packaging is allowed, but it is derived from the canonical session package rather than redefining it

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

## Prepared data vs consumer packages

The public model distinguishes three layers:

1. Canonical prepared data
   - session-scoped data rooted at `sessions/ses-<id>/`
   - raw streams plus explicit session metadata and sync declarations
2. Canonical annotation layer
   - `events.tsv` in `t_session`
   - optional `events.json` for extra-column semantics
3. Consumer-facing derived products
   - proxies, thumbnails, browser manifests, runtime-specific deploy bundles
   - useful for a named consumer, but not required dataset prerequisites

This matters because consumer-specific runtime needs should not silently redefine the canonical dataset contract.

## Timing and synchronization

Canonical session time:
- `t_session`: seconds from session start (float; `0 = session start`)

Each stream should declare its native timebase in a sidecar:
- `raw/<stream_type>/<stream_id>/<stream_id>_stream.yaml`

If a stream is aligned into `t_session`, the alignment should be represented explicitly:
- `derived/sync/timebase_maps/<stream_id>_timebase_map.json`

Recommended session-level evidence:
- `derived/sync/sync_markers.tsv`
- `derived/sync/reports/<name>.json`

Public policy for sync state:
- `native_aligned`: already synchronized by acquisition/runtime design and declared explicitly
- `declared_mapping`: a known offset/scale or equivalent mapping is declared explicitly
- `inferred_mapping`: synchronization was estimated, corrected, stitched, or reconstructed and therefore requires explicit artifacts plus provenance

Tools must not treat "it loads" as proof that streams are synchronized.

## Resultbundle seam

Result bundles are typed, versioned outputs that can be handed off safely across plugins or processing stages.

A materialized result bundle should include `resultbundle.json`.

Required fields:
- `resultbundle_type`
- `schema_version`
- `time_reference`
- `files[]`

Recommended fields:
- `created_at`
- `producer`
- `upstream_tool`
- `source`
- `primary_keys`

Minimal validation in v0.1 is intentionally lean:
- validate the envelope
- check required files
- check required join/time keys
- allow unknown extra fields and columns

Key portability rule:
- do not rewrite vendor columns in place just to satisfy tooling
- use `files[].key_columns` to map normalized join/time keys to native column names

## Annotation pivot

Use `events.tsv` as the canonical public annotation pivot.

Required columns:
- `onset`
- `duration`
- `label`
- `tier`

Recommended columns:
- `person_uid`
- `event_id`

Optional:
- `parent_id`
- `annotator`
- `stream_id`
- `comment`
- `confidence`
- `source_tool`
- additional documented columns via `events.json`

The intended role of `events.tsv` is roundtripping across tools without making any one tool's local CSV shape the public contract.

## Status

This remains a draft public summary. Exact filenames, schemas, and exporter details may still evolve, but the session-scoped data model, explicit sync-state requirement, and `events.tsv` annotation pivot are the current steering baseline.
