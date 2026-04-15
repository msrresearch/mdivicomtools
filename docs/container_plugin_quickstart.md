# Container Plugin Preview (Docker, current scaffold)

This guide shows the expected command shape for container plugins and the
current runtime caveats in the public core. It is a preview for plugin authors,
not a claim that docker execution is already implemented end to end.

## Current Status

- The CLI exposes `--backend docker` in `mdivicom run`.
- In this repository version, docker execution is scaffold-only and currently
  returns `NotImplementedError`.
- Use this document as a preview of the intended command shape for plugin authors and wrappers.

## Prerequisites

- Docker Engine installed and available on PATH.
- A plugin package registered under `mdivicomtools.plugins` with:
  - `meta.kind = "container"`
  - container execution metadata (for example image, argv, and mount conventions)
    in its plugin payload/manifest once the container lane is implemented.

## Expected Runtime Model

Container plugins should be executed with:

- dataset mounted read-only
- output directory mounted read-write
- optional work directory mounted read-write

The runner should capture run-level provenance:

- plugin id/version
- backend
- config hash
- start/end timestamps
- exit status
- container image tag/digest (if available)

## Command Forms

List installed plugins:

```bash
mdivicom plugins list
```

Inspect plugin metadata:

```bash
mdivicom plugins info <publisher>/<plugin_id>
```

Run a plugin with explicit docker backend:

```bash
mdivicom run <publisher>/<plugin_id> \
  --dataset /path/to/dataset \
  --out /path/to/out \
  --backend docker
```

Optional dry-run shape:

```bash
mdivicom run <publisher>/<plugin_id> \
  --dataset /path/to/dataset \
  --out /path/to/out \
  --backend docker \
  --dry-run
```

## Caveat for This Public Core Version

If you run `--backend docker` today, expect a scaffold error until container
backend execution is implemented in runtime:

```text
NotImplementedError: docker backend is not implemented in this scaffold yet
```

## Recommendation for Plugin Authors

- Keep container plugin metadata JSON-safe so `plugins list/info` remains fast.
- Publish at least one minimal smoke fixture and expected command line in your
  plugin repo docs.
- For cross-plugin outputs, emit `resultbundle.json` sidecars and validate with
  `mdivicom resultbundles validate`.
