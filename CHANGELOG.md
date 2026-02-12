# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Changed
- Clarified plugin-first public usage in `README.md` and removed submodule-oriented setup guidance.
- Moved the MDI versioning/release policy to public docs (`README.md`), replacing the prior `AGENTS.md` publication path.
- Updated release checks to validate policy presence in `README.md` or `docs/RELEASE.md`.

### Removed
- Removed `tools/mdipplcloud` submodule pointer from the public core repository.
- Removed tracked `AGENTS.md` policy artifact from the public repository root.

## [0.2.0] - 2026-02-11

### Added
- Release tooling scripts under `scripts/release/` for version bumping, release checks, and annotated tagging.
- `docs/RELEASE.md` with the `local/dev -> local/release-staging -> main` promotion workflow.
- Plugin-first README onboarding and bundle-install guidance.
- Draft public contracts under `docs/` for plugin interface and openSIDS/resultbundle interoperability seam.

### Changed
- `pyproject.toml` package version normalized to SemVer format (`0.2.0`).
- Added Makefile release targets: `release-check`, `release-bump-*`, and `release-tag`.

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
