# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

### Added
- Release tooling scripts under `scripts/release/` for version bumping, release checks, and annotated tagging.
- `docs/RELEASE.md` with the `local/dev -> local/release-staging -> main` promotion workflow.

### Changed
- `pyproject.toml` package version normalized to SemVer format (`0.2.0`).
- Added Makefile release targets: `release-check`, `release-bump-*`, and `release-tag`.

### Fixed
- Established a consistent release-policy baseline for this repository.
