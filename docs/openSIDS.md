# openSIDS (public draft)

Status:
- public draft
- document version: `v0.2`

## What openSIDS is

openSIDS is a draft data model for multimodal social-interaction research. It is inspired by BIDS and intended to remain compatible with BIDS-style workflows and later BIDS export, but it is designed first around the practical needs of social-interaction datasets.

It is meant for prepared datasets that include:
- recordings with multiple people
- multiple streams such as video, audio, gaze, or IMU
- explicit synchronization and time-mapping information
- annotations that need to round-trip across tools
- derived outputs that later tools need to consume safely

Researchers often start from a mix of acquisition folders, annotation exports, and processing outputs rather than from a single clean standard layout. openSIDS aims to give those datasets a shared source of truth so that different tools can work from the same assumptions.

## Current Scope

The current draft focuses on a few main choices:
- the main unit is the **session**
- the main time axis is `t_session`
- one session can contain multiple persons and multiple streams
- annotations are represented through `events.tsv`, with optional `events.json`
- derived outputs that need handoff should be described with `resultbundle.json`
- BIDS compatibility matters, but detailed BIDS export behavior remains follow-on work

This draft does not try to settle everything yet. It is not:
- a frozen final standard
- a complete BIDS export recipe for every modality
- a full validation scheme for every result bundle family
- a workflow engine or deployment system

## The core mental model

If you remember only a few things about openSIDS, they should be these:

1. A **session** is the main prepared-data unit.
2. A session is one declared timing domain.
3. The main time axis is `t_session`, in seconds from an explicitly declared session start.
4. A session can contain multiple **persons** and multiple **streams**.
5. Annotations are represented through `events.tsv`.
6. Tool-specific or UI-specific packages are derived views over the session package, not replacements for it.
7. Result bundles describe derived outputs that need safe handoff.

## A simple example

Imagine a dyadic conversation study with:
- two participants
- two eye trackers
- one room camera
- separate audio streams
- manual annotations
- downstream derived outputs such as sync maps, transcripts, or overlays

In openSIDS, that would normally be represented as:
- one main **session**
- multiple **persons** within that session
- multiple **streams** within that session
- explicit mappings from each stream's native timebase into `t_session`
- one shared annotation representation (`events.tsv`)
- optional derived outputs described as result bundles

The important point is that the session, not any single consumer tool, defines the timing and structure.

## Typical layout (illustrative)

```text
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

This layout is illustrative rather than exhaustive. The main idea is that the dataset manifest points to session roots, and each session root contains the metadata needed to interpret persons, streams, time, annotations, and derived outputs.

Authority and inference:
- dataset/session manifests and metadata files ("sidecars") take precedence when present
- importers may use best-effort inference only when those files are missing or incomplete
- if tools infer missing structure from legacy inputs, they should warn clearly and emit generated manifests or sidecars when possible

## Identifiers and naming

The main identifiers are:
- session id: `ses-<id>`
- session manifest: `ses-<id>_session.yaml`
- dataset-stable person id: `person_uid` (recommended shape: `sub-*`)
- optional session-local alias: `person_id` (recommended shape: `per-*`)
- stream id: `str-<id>`

Useful metadata can also include:
- optional `encounter_id`
- optional `interaction_id`
- optional `interaction_kind`
- `task`
- `run_index`
- optional `run_label`
- optional `topic_id`

Important rules:
- `ses-<id>_session.yaml` is a session-wide metadata file, not a sync-only auxiliary file
- `task` and `run_index` describe analysis or export semantics; they do not define synchronization
- `pipeline_run_id` should be used for execution provenance, so it is not confused with `run_index` or BIDS-style `run-*` semantics
- logical ids and manifests take precedence, while folder labels such as `dyad-01` or `run-01` are human-readable convenience labels
- `role` is useful metadata, but it is not an identifier and must not replace `person_uid`
- if roles change over time within a session, represent those changes as annotations in `events.tsv` rather than by changing identifiers

## Key concepts

### Session

A session is the main prepared-data unit and one declared timing domain. If acquisition restarts and creates a new timing domain, that should normally become a new session.

### Encounter

An encounter is an optional grouping above the session level, useful when one visit or interaction episode contains multiple acquisition restarts. An encounter is not itself a synchronization domain.

### Interaction

An interaction is a grouping within a session, such as a dyad or group context. `interaction_id` and `interaction_kind` can be useful metadata for analysis and export, but they do not replace the session as the core timing unit.

### Person

openSIDS keeps multi-person structure explicit. The main identifier is a dataset-stable `person_uid` (recommended shape: `sub-*`). A shorter session-local alias such as `person_id` (recommended shape: `per-*`) may be used for convenience, but it must map back to `person_uid`.

### Stream

A stream is a concrete data source within a session, such as a camera, microphone, eye tracker, or IMU stream. Each stream has its own native clock or timestamp system and may need an explicit mapping into session time.

### Annotation

Annotations are represented through a shared format so that they can round-trip across tools without making any one tool's export format the public standard.

### Result bundle

A result bundle is a typed, versioned derived output that one tool can hand off to another. Examples include sync artifacts, overlays, transcripts, or feature outputs.

## Timing and synchronization

Timing is one of the main reasons openSIDS exists.

Canonical session time:
- `t_session`: seconds from the declared session start (`0 = session start`)

Expected metadata:
- `ses-<id>_session.yaml` should declare the sync reference that defines `t_session=0`
- the `sync_reference` block should include at least a reference `stream_id`, a `zero_event`, and a human-readable `definition`
- `raw/<stream_type>/<stream_id>/<stream_id>_stream.yaml` should describe each stream's native clock or timestamp system

If a stream is aligned to `t_session`, that alignment should be represented explicitly:
- `derived/sync/timebase_maps/<stream_id>_timebase_map.json`

Public mapping model:
- the required baseline is an `affine` mapping: an offset plus optional scale correction
- in the simplest case, that can be just an offset (`scale = 1.0`)
- `piecewise_linear` mappings are allowed when drift or nonlinearity matters
- `lookup_table` mappings are optional when exact per-frame or per-sample mappings are needed

Recommended session-level evidence:
- `derived/sync/sync_markers.tsv`
- `derived/sync/reports/<name>.json`

`sync_markers.tsv` can be used as a long-form table of observed marker times across streams when synchronization is established or checked from explicit marker evidence.

Public sync-state categories:
- `native_aligned`: streams are already synchronized by acquisition or runtime design, and that is declared explicitly
- `declared_mapping`: an explicit offset, scale, or similar mapping is declared
- `inferred_mapping`: synchronization was estimated, corrected, stitched, or reconstructed and therefore requires explicit artifacts plus a record of how the mapping was produced

When sync artifacts are required:
- if timing compatibility is already trustworthy and explicitly declared, a heavy reconstruction artifact set is not required
- if timing is inferred, corrected, stitched, drift-adjusted, or otherwise non-trivial, explicit sync artifacts and QC/provenance are required

Practical rule:
- tools must not treat "it loads" as proof that streams are synchronized

Edge cases such as variable-frame-rate sources, dropped or duplicated frames/samples, and device clock resets or discontinuities should be treated as first-class timing issues rather than ignored.

## Common annotation representation

The openSIDS public annotation representation is `events.tsv`, with optional `events.json` for additional column semantics.

More generally, **annotations** are the broader research objects: human-coded labels, intervals, notes, role changes, or other interpretations attached to persons, streams, or sessions over time. In openSIDS, those annotations are represented in `events.tsv`. Tool-specific formats are still allowed, but they are treated as import/export surfaces around the same shared event representation rather than as competing public formats.

Required columns:
- `onset`
- `duration`
- `label`
- `tier`

Recommended columns:
- `person_uid`
- `event_id`

Optional examples:
- `parent_id`
- `annotator`
- `stream_id`
- `comment`
- `confidence`
- `source_tool`

A codebook should document label meanings and any extra columns. The minimal public option is to document them in `events.json`, though a dataset-level codebook is also acceptable.

This is meant to support round-tripping across tools such as ELAN, BORIS, and related workflows without making one local CSV format the public standard.

## Derived outputs and result bundles

openSIDS distinguishes prepared session data from **derived outputs** such as sync artifacts, transcripts, overlays, features, or tool-specific exports.

When a derived output is meant to be consumed by another tool or processing step, it should be described as a **result bundle**. The purpose of a result bundle is to make handoff safer and less ambiguous: a downstream tool should be able to tell what the output is, what files belong to it, and how its timing and join keys should be interpreted.

In a BIDS export, derived outputs should generally live in a **BIDS Derivatives** dataset. `resultbundle.json` is not intended as an alternative to BIDS Derivatives. Instead, it is a portable handoff manifest that can live inside a derivative dataset when generic BIDS naming and metadata are not enough for safe downstream consumption.

A materialized result bundle should include `resultbundle.json`.

Minimum required fields:
- `resultbundle_type`
- `schema_version`
- `time_reference`
- `files[]`

Recommended fields:
- `source_scope`
- `producer`
- `upstream_tool`
- `source`
- `primary_keys`
- `created_at`

Practical rules:
- metadata in `resultbundle.json` takes precedence when present
- if the sidecar is detached from the payload root, it should point back to the payload via `source`
- if a legacy or vendor export has no sidecar, tools may infer a provisional bundle description, but they should warn clearly and write a generated sidecar when possible
- tools should not rewrite vendor columns in place just to satisfy openSIDS tooling
- use `files[].key_columns` to map normalized join or time keys to native column names
- use `files[].time` to distinguish point-like time from interval-like time

Current validation is intentionally lean:
- validate the basic bundle structure
- check detached-sidecar path portability
- check required files
- optionally check type/version compatibility
- defer per-type join and time-key validation
- allow unknown extra fields and columns

This keeps the handoff layer useful without pretending that the current draft already standardizes every derived-output family in detail.

## Core Data vs Tool-Specific Packages

openSIDS distinguishes between:
- prepared data
- shared annotations
- tool-specific or UI-specific derived packages

That distinction matters because downstream consumers often need extra products such as thumbnails, browser manifests, low-resolution proxies, or deployment bundles. Those may be useful and sometimes necessary, but they should be treated as derived products on top of the session package rather than as the dataset itself.

Practical safety rules:
- aggregating multiple session-scoped entries for a consumer or workflow is allowed, but that aggregation does not imply a shared cross-session timebase unless that is declared separately
- consumer-specific packages should record how they were produced and must not silently be treated as original source data
- if a workflow depends on consumer-facing packages that are absent, tools should fail clearly or request an explicit preparation step rather than improvising silently

## Relation to BIDS

openSIDS is designed to stay compatible with later export into BIDS-like views, but the current draft does not try to settle every BIDS export detail.

The current direction is:
- keep the main model openSIDS-first
- keep BIDS compatibility in mind
- defer strict export behavior and validator strategy to later hardening work

Current BIDS status:
- BIDS export is a follow-on or export-view question rather than the main thing this draft is trying to settle
- behavioral raw audio/video support in BIDS is still evolving, so detailed export naming should be treated as provisional
- the public draft here describes the openSIDS model, not a fully settled BIDS export recipe

### BEP 047 compatibility

The current draft is intended to stay broadly compatible with the BEP 047 direction for behavioral recordings in BIDS.

Current compatibility direction:
- keep the openSIDS model session-first and multi-person-first; treat BEP 047 as an export view for raw behavioral recordings rather than as the internal model
- when exporting raw recordings into BIDS, align with BEP 047 behavioral-recording suffixes and entities where appropriate
- keep stronger timing and synchronization semantics in openSIDS metadata and sync artifacts rather than assuming that raw BIDS recording layout alone is enough to express them
- treat BIDS Derivatives as the dataset-level home for derived outputs in BIDS exports, while allowing `resultbundle.json` inside derivative datasets when extra tool-facing handoff semantics are needed
- treat detailed behavioral audio/video export mapping as provisional while BEP 047 remains under active development

## Current draft status

This file is the current public-facing draft of openSIDS. It is intended to explain the model clearly enough for new readers while still keeping the main structure visible.

For deeper normative detail, background decisions, and deferred items, the steering draft in this repository remains more detailed than this public page.
