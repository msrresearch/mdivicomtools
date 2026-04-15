# Bundle Presets

This folder provides release-ready install presets for common onboarding cases.

Available presets:

- `requirements-core.txt`
  - installs only the public `mdivicomtools` core package
- `requirements-core-mdipplcloud.txt`
  - installs the core plus the public `mdipplcloud` plugin

Install examples:

```bash
pip install -r bundles/requirements-core.txt
pip install -r bundles/requirements-core-mdipplcloud.txt
```

Reproducibility note:

- These presets are pinned to release tags for reproducible public installs.
- Use `@main` only for explicit development installs outside the release presets.
- Keep all URLs public-safe (no private remotes, tokens, or internal paths).
