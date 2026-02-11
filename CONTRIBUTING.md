# Contributing & Maintenance Policy (minimal)

This repository is **public**. Please keep all changes safe to publish.

## Public safety (non‑negotiable)

- Never commit **sensitive** material (PHI, identifiable clinical media, private datasets, credentials, internal hostnames/paths, private repo URLs, etc.).
- Keep examples and fixtures **synthetic or de‑identified**.
- If you’re unsure whether something is safe to publish: **don’t push it** (open an issue first).

## Branching model

We use a simple trunk-based workflow:

- Default branch: `main`
- Work happens on short‑lived branches:
  - `feat/<topic>` new features
  - `fix/<topic>` bug fixes
  - `docs/<topic>` documentation
  - `chore/<topic>` maintenance/refactors

Policy:
- Avoid direct commits to `main` (prefer PRs).
- Keep PRs small and focused (one intent per PR).

## Review / PR policy

- Non-trivial changes should get at least **one review** before merging.
- If a change affects the **public contract** (CLI surface, plugin contract, dataset conventions), it must:
  - update docs, and
  - clearly state migration/compat impact in the PR description.

## Versioning / releases

- Version is tracked in `pyproject.toml`.
- Tag releases as `v<version>` (e.g., `v0.2.0`).
- Until the v0.1 contracts stabilize, prefer frequent small releases; avoid breaking changes without a clear rationale.

## Development cycle (practical)

- Prefer “docs + minimal scaffolding” first, then implementations in small steps.
- Heavy or conflicting dependencies should be isolated behind plugins (docker/tool lane when needed) rather than added to the core environment.
- Git submodules may exist for developer convenience, but the default end‑user story should not require them.

