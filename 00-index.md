# Index of Docs

This project has the following documents, each with one job. Don't blur these responsibilities.

| # | Doc | Responsibility |
|---|-----|-----------------|
| 1 | [00-index.md](00-index.md) | This file. Map of the project — what each doc does and where things live. |
| 2 | [way-of-working.md](way-of-working.md) | How we (human + AI) operate this project. The workflow/process doc. |
| 3 | [requirements.md](requirements.md) | What the website should be/do. Source of truth for desired behavior. |
| 4 | [index.html](index.html) | Landing page with links to each World Cup. |
| 5 | [2018.html](2018.html) / [2022.html](2022.html) / [2026.html](2026.html) | The implementation — one page per World Cup. Should always match requirements.md. |
| 6 | [shared.js](shared.js) | Shared rendering logic included by all three World Cup pages. |
| 7 | [scale-algorithm.md](scale-algorithm.md) | Deep-dive on the Scale view layout: height algorithm, horizontal dodge (Pass 1 + Pass 2), constants, and implementation pitfalls. Update when the scale rendering logic changes. |
| 8 | [scripts/build.py](scripts/build.py) | Regenerates embedded data in all HTML pages from `data/*.json`. Run after any data edit. |
| 9 | [scripts/set_result.py](scripts/set_result.py) | Enters a game result and calls build.py. The normal data-entry path. |
