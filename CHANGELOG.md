# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

## [0.3.0] - 2026-04-15

### Added
- Resultbundle validation policy profiles (`local_default`, `plugin_strict`,
  `pipeline_auto`, `legacy_off`) in
  `mdivicomtools.resultbundles.policy`.
- CLI support for policy-based validation:
  - `mdivicom resultbundles validate --policy <profile>`
  - `mdivicom resultbundles policies`
- Integration note:
  - `docs/resultbundle_runtime_integration.md`
    (operating model + migration guidance for plugin repos).
- Curated onboarding bundle presets in `bundles/`:
  - `requirements-core.txt`
  - `requirements-core-mdipplcloud.txt`
  - `bundles/README.md`
- `docs/container_plugin_quickstart.md` with docker/container command forms and
  scaffold caveats for the current public core.

### Changed
- Bumped the public core package version to `0.3.0`.
- Added release-pinned install presets and README examples for the public core
  (`v0.3.0`) and `mdipplcloud` (`v0.2.0`).
- Documented CLI/API integration seam and local-vs-plugin validation defaults in:
  - `README.md`
  - `docs/archive/openSIDS.md`
  - `docs/plugin_contract.md`
- Updated onboarding docs to point to curated `bundles/` presets and linked the
  container quickstart from README/docs index.
- Corrected the public `openSIDS` draft to describe the current resultbundle
  validation surface accurately.

### Fixed
- Strict resultbundle validation now anchors detached `source.root` under the
  selected base root and reports non-portable roots in non-strict modes.
- `scripts/release/release_check.sh` now accepts both the legacy MDI policy
  headings and the current `Versioning and releases` headings.

## [0.2.0] - 2026-02-11

### Added
- `mdivicomtools.resultbundles` runtime primitives for v0.1 interop:
  - detached sidecar resolution (`source.root` + `source.root_base`)
  - minimal envelope validation
  - type/version compatibility checks
- New CLI commands:
  - `mdivicom resultbundles inspect`
  - `mdivicom resultbundles validate`
- Release tooling scripts under `scripts/release/` for version bumping, release checks, and annotated tagging.
- `docs/RELEASE.md` with the `local/dev -> local/release-staging -> main` promotion workflow.
- Plugin-first README onboarding and bundle-install guidance.
- Draft public contracts under `docs/` for plugin interface and openSIDS/resultbundle interoperability seam.
- Initial tests for resolver escape guards, warn-mode validation behavior, and compatibility checks.

### Changed
- `pyproject.toml` package version normalized to SemVer format (`0.2.0`).
- Added Makefile release targets: `release-check`, `release-bump-*`, and `release-tag`.
- Clarified plugin-first public usage in `README.md` and removed submodule-oriented setup guidance.
- Consolidated MDI versioning/release policy into public docs and updated release checks to validate policy presence in `README.md` or `docs/RELEASE.md`.

### Removed
- Removed `tools/mdipplcloud` submodule pointer from the public core repository.

### Fixed
- Normalized plugin discovery/runtime to support v0.1 `meta`/`entry.callable` plugin contracts (including mdipplcloud-style registration).

## [0.1.0] - 2025-04-10

### Added
- Initial public repository structure and package scaffolding (`pyproject.toml`, requirements, license, README baseline).
- Initial `mdivicomtools` Python package with core namespace exports and utilities.

### Changed
- Early documentation refinements for installation and project context.

### Fixed
- Initial cleanup and namespace/logging consistency fixes across early commits.
