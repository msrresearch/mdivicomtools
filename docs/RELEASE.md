# Versioning and releases

## Version source

- Python packages: `pyproject.toml` (`[project].version`)
- Non-package repos: `VERSION`

## Public versioning

- Package/tool releases use Semantic Versioning (`MAJOR.MINOR.PATCH`).
- Schema/interface compatibility versions should be tracked separately inside contracts and sidecars.

## Publish flow

- Prepare the release content on a maintainer branch.
- Open a PR to `main` and merge according to branch protection.
- If linear history/no merge commits is enforced, use squash/rebase merge.

## Commands

```bash
make release-check
make release-bump-patch
# or make release-bump-minor / make release-bump-major
```

After merge to `main`:

```bash
make release-tag
# then push tags explicitly
# git push origin refs/tags/vX.Y.Z
```

## Changelog policy

- Keep `## [Unreleased]` at top.
- Add release section `## [X.Y.Z] - YYYY-MM-DD` for each release.
- Maintain concise entries grouped under Added/Changed/Fixed.
