# Way of Working

A tiny project: a requirements doc + an implementation. Keep it that way.

## The loop

1. **Update requirements** — Human (with AI help) edits `requirements.md` to describe a desired change.
2. **Update implementation** — AI reads `requirements.md` and updates the implementation to match it.
3. **Review** — Human opens the implementation in a browser and checks it matches what `requirements.md` describes.
4. Repeat.

## Rules of thumb

- `requirements.md` describes *what* the site should do/look like, including scope/structure (e.g. single page vs multiple) — that's defined there, not here.
- `requirements.md` is the source of truth. If the implementation and `requirements.md` ever disagree, that's a bug — fix one to match the other.
- Keep the implementation as simple as `requirements.md` allows — no build steps, frameworks, or dependencies. Just open the file(s) in a browser.
