# mdivicomtools

**mdivicomtools** is the public core for modular multimodal dataset preparation and analysis workflows: a Python-based package with a lightweight CLI, shared contracts, and plugin discovery so separate tools can interoperate without forcing one shared dependency stack, developed as part of the [mdinteract](https://vicom.info/projects/multimodal-assessment-of-dyadic-interaction-in-disorders-of-social-interaction) project within the DFG Priority Program Visual Communication ([ViCom](https://vicom.info)) and specifically tailored for research in multimodal visual communication.

This repository provides the public core package, the current openSIDS draft, and resultbundle interoperability tooling. It is a stable public starting point for the ecosystem, while broader end-to-end workflows still depend on separate plugins and companion repositories.

## Start here

- `docs/openSIDS.md` - current public draft of the session, sync, annotation, and resultbundle model (`v0.2`)
- `docs/plugin_contract.md` - plugin registration and run interface draft (`v0.1`)
- `docs/resultbundle_runtime_integration.md` - producer/consumer seam for `resultbundle.json` (`v0.1`)
- `docs/container_plugin_quickstart.md` - preview of container-lane command shape and current caveats
- `bundles/README.md` - curated install bundles for common local setups

The intended modular interoperability pattern is:

```text
data-producing application or tool -> openSIDS-compatible dataset/session view -> installed plugin(s) -> ResultBundle(s) -> independent consumer
```

Originating applications and tools keep their source-specific acquisition,
import, processing, or study-workflow responsibilities. openSIDS provides the
portable data/session boundary, the plugin contract provides the execution
boundary, and ResultBundles provide typed outputs for independent consumers.

## What works today

- Python-lane plugin discovery and execution via `mdivicom`
- Resultbundle inspection and validation helpers for cross-tool handoff checks
- Curated install bundles for common local setups

## What is still draft or scaffold

- openSIDS is still a draft contract, not a frozen standard
- `mdivicom run ... --backend docker` is scaffold-only and currently raises `NotImplementedError`
- Broader end-to-end orchestration is still plugin- and script-oriented rather than a finished workflow engine
- Domain-specific plugins live in separate repos and must be installed separately

## Quick Start Guide

### Installation for Users

The default end-user story does **not** require git submodules. Install the core, then install plugins as needed.

Use a Python virtual environment (recommended):

```bash
# python venv
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
# conda
conda create -n mdivicomtools python=3.10
conda activate mdivicomtools  

```

For the public `v0.3.0` release, install the core from a pinned Git tag:

```bash
pip install -U pip
pip install git+https://github.com/msrresearch/mdivicomtools.git@v0.3.0
```

### Install plugins (optional)

Plugins are separate packages that register themselves via Python entry points (`mdivicomtools.plugins`). Install only what you need.

Example optional plugin:

```bash
pip install git+https://github.com/msrresearch/mdipplcloud.git@v0.2.1
```

### Install core + a plugin bundle

Use curated bundle presets from `bundles/`:

```bash
pip install -r bundles/requirements-core.txt
pip install -r bundles/requirements-core-mdipplcloud.txt
```

For development against the moving main branch instead of a release tag, use explicit `@main` installs outside these presets.

Then inspect what is available:

```bash
mdivicom plugins list
mdivicom plugins info <plugin_id>
```

### Container plugin preview

The expected container-lane command shape and current runtime caveats are documented in:

- `docs/container_plugin_quickstart.md`

Current caveat for this public core version:
- `mdivicom run ... --backend docker` is scaffold-only and currently raises `NotImplementedError`.

### Resultbundle inspection and validation

For stronger producer-to-consumer interoperability, emit a `resultbundle.json` sidecar with at least `resultbundle_type`, `schema_version`, `time_reference`, and `files[]`.

```bash
mdivicom resultbundles inspect --sidecar /path/to/resultbundle.json --out-dir /path/to/run_out
mdivicom resultbundles validate --sidecar /path/to/resultbundle.json \
  --out-dir /path/to/run_out \
  --mode strict \
  --expect-type mdivicom.timeline.subject \
  --supported-major 0
mdivicom resultbundles policies
```

Validation modes:
- `strict`: fail on invalid envelope, missing required files, or incompatible type/version
- `warn`: continue with explicit warnings for softer compatibility issues
- `off`: skip validation checks

See `docs/resultbundle_runtime_integration.md` for the fuller contract and policy profiles.

### Setup for Developers

To contribute or develop locally:

```bash
git clone https://github.com/msrresearch/mdivicomtools.git
cd mdivicomtools
pip install -e .
```

Install plugins as separate packages in the same environment when testing integration behavior:

```bash
pip install -e /path/to/plugin_repo
```

There is also a dev-only source-tree discovery path for local integration work:

```bash
MDIVICOM_DEV_PLUGIN_ROOTS=/path/to/plugin_roots .venv/bin/python -m mdivicomtools plugins list
```

That environment-variable path is opt-in only and does not change default public behavior.

### Logging Setup

**mdivicomtools** provides convenient logging setups. For quick usage, just call `setup_logging()`:

```python
from mdivicomtools.utils import setup_logging
setup_logging(preset="console_debug")
```

#### Available Presets
- **`console_debug`**  
  All messages at DEBUG level and above go to the console.
- **`console_info_file_debug`**  
  INFO-level messages go to the console, and DEBUG-level messages are saved to `mdivicomtools_debug.log`.
- **`json_console_debug`**  
  DEBUG-level messages to console, formatted as JSON (requires `python-json-logger`).

#### Advanced Usage
For custom logging setups, pass your own dictionary config:
```python
my_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": { ... },
    "root": { ... }
    # etc.
}
setup_logging(dict_config_override=my_config)
```
Or configure Python’s `logging` manually without calling `setup_logging()`.

---

## Contributing

Contributions are welcome! Follow these steps:

1. Fork and clone your fork.
2. Create a feature branch (`git checkout -b feat/<new-feature>`).
3. Develop and test changes.
4. Push changes and open a Pull Request.

---

## Versioning and releases

- Package/tool releases use Semantic Versioning (`MAJOR.MINOR.PATCH`).
- The package version source of truth is `pyproject.toml` (`[project].version`).
- Schema/interface compatibility versions are tracked separately inside contracts, sidecars, and interface docs.
- `CHANGELOG.md` keeps `## [Unreleased]` at the top and release sections for published versions.
- Published releases are tagged as `vX.Y.Z` from `main`.
- Public release commands are documented in `docs/RELEASE.md`.

---

## Roadmap

- Expand core module features
- Add more plugins (python + container)
- Automated integration testing
- Publish to PyPI

---

## Citation
If you use this code in your research, please cite
- www.github.com/msrresearch/mdivicomtools

---

## License

This repository is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

(c) 2025 Martin Schulte-Rüther and the mdinteract project team

---

## Acknowledgements
This project was supported by the following grants to Martin Schulte-Rüther
DFG SCHU-2493/5-1 (Deutsche Forschungsgemeinschaft), LSC-AF2023_04 and LSC-AF2021_05 (Leibniz ScienceCampus).

## Contact
Martin Schulte-Rüther

Department of Child and Adolescent Psychiatry and Psychotherapy, University Hospital Heidelberg, Ruprechts-Karls-University Heidelberg, [martin.schulte-ruether@uni-heidelberg.de](mailto:martin.schulte-ruether@uni-heidelberg.de)

Department of Child and Adolescent Psychiatry and Psychotherapy, University Medical Center Göttingen, martin.schulte-ruether@med.uni-goettingen.de


For questions or issues, please open an issue or contact the maintainers directly.
