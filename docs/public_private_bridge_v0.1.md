# Public↔private bridge v0.1 (draft)

## Principle

- The public core (`mdivicomtools`) defines **contracts** (CLI + IO + provenance) and stays publishable.
- Private/internal code ships as optional plugins that depend on the public core (never the other way around).

## Hard rule

The public repo must never reference private repos/resources:
- no private URLs
- no private submodules
- no private package indexes in docs

## Submodules

Submodules can be convenient for internal development, but they should not be the default end-user installation story.

