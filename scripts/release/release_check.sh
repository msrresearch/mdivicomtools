#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

pass() {
  echo "[OK]   $1"
}

if [[ ! -f CHANGELOG.md ]]; then
  fail "CHANGELOG.md missing"
fi
pass "CHANGELOG.md exists"

if ! grep -q '^## \[Unreleased\]' CHANGELOG.md; then
  fail "CHANGELOG.md has no [Unreleased] section"
fi
pass "CHANGELOG.md has [Unreleased]"

if [[ -f pyproject.toml ]] && awk '
  /^\[project\]/ {in_project=1; next}
  /^\[/ && in_project {in_project=0}
  in_project && /^version *= *"[^"]+"/ {found=1}
  END {exit(found ? 0 : 1)}
' pyproject.toml; then
  pass "pyproject.toml [project].version found"
elif [[ -f VERSION ]]; then
  pass "VERSION file found"
else
  fail "No version source (pyproject.toml [project].version or VERSION)"
fi

if [[ -f README.md ]] && grep -q '^## MDI Versioning and Release Policy' README.md; then
  pass "README.md includes MDI version policy section"
elif [[ -f docs/RELEASE.md ]] && grep -q '^# Release Workflow (MDI policy)' docs/RELEASE.md; then
  pass "docs/RELEASE.md includes MDI release policy"
else
  fail "No MDI release policy found (expected README.md section or docs/RELEASE.md)"
fi

echo "Release checks passed."
