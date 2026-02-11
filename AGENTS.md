<!-- BEGIN MDI VERSION POLICY -->
## MDI Versioning and Release Policy (v1)

- Use Semantic Versioning (`MAJOR.MINOR.PATCH`) for tool/package releases.
- Keep data/schema compatibility versioning separate (for example `schema_version` in contracts/sidecars).
- Version source of truth:
  - Python package repos: `pyproject.toml` (`[project].version`)
  - Non-package repos: root `VERSION` file
- Branch flow for releases:
  - `local/dev` for integration
  - `local/release-staging` for release candidates
  - `main` for publication
- Cherry-pick only non-`plan:` commits into release candidates.
- Maintain `CHANGELOG.md` with `## [Unreleased]` at top.
- Create annotated tags as `vX.Y.Z` from `main` only.
- Use installed release tooling:
  - `scripts/release/bump_version.sh [patch|minor|major]`
  - `scripts/release/release_check.sh`
  - `scripts/release/tag_release.sh`
- Keep tag pushing explicit (no auto-push in scripts).

### Commit message convention (recommended)

- Prefix with one of: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `perf`, `build`, `ci`.
- Keep release commits focused (`chore: release vX.Y.Z`).
<!-- END MDI VERSION POLICY -->
