# Index of Docs

This project has the following documents, each with one job. Don't blur these responsibilities.

## Project docs (not deployed)

| # | Doc | Responsibility |
|---|-----|----------------|
| 1 | [00-index.md](00-index.md) | This file. Map of the project — what each doc does and where things live. |
| 2 | [way-of-working.md](way-of-working.md) | How we (human + AI) operate this project. Workflow, process, brand, visual direction. |
| 3 | [requirements.md](requirements.md) | What the World Cup ELO feature should be/do. Source of truth for desired behavior. |
| 4 | [brand.md](brand.md) | SportsOnTheInternet brand: concept, audience, voice, visual direction. |
| 5 | [scale-algorithm.md](scale-algorithm.md) | Deep-dive on the Scale view layout algorithm. Update when scale rendering logic changes. |
| 6 | [scripts/build.py](scripts/build.py) | Regenerates HTML pages in site/ from data/*.json and shared.js/shared.css. |
| 7 | [scripts/set_result.py](scripts/set_result.py) | Enters a game result and calls build.py. The normal data-entry path. |
| 8 | [scripts/set_team_elo.py](scripts/set_team_elo.py) | Sets a team's initial ELO and calls build.py. |
| 9 | [data/](data/) | Source data: 2014.json, 2018.json, 2022.json, 2026.json, teams.json. Not deployed directly. |

## Site (deployed)

Everything under `site/` is what goes online. The static host points at this folder.

| Path | Responsibility |
|------|----------------|
| [site/index.html](site/index.html) | SportsOnTheInternet homepage. |
| [site/football/worldcup/history.html](site/football/worldcup/history.html) | Year-over-year knockout comparison (F4/F8/F16). Build artifact — do not edit directly. |
| [site/football/worldcup/2014.html](site/football/worldcup/2014.html) | World Cup 2014 page. Build artifact — do not edit directly. |
| [site/football/worldcup/2018.html](site/football/worldcup/2018.html) | World Cup 2018 page. Build artifact — do not edit directly. |
| [site/football/worldcup/2022.html](site/football/worldcup/2022.html) | World Cup 2022 page. Build artifact — do not edit directly. |
| [site/football/worldcup/2026.html](site/football/worldcup/2026.html) | World Cup 2026 page. Build artifact — do not edit directly. |
| [site/football/worldcup/flags/](site/football/worldcup/flags/) | Flag SVGs served alongside the World Cup pages. |
| [shared.js](shared.js) | Shared JS source — inlined into World Cup pages at build time. |
| [shared.css](shared.css) | Shared CSS source — inlined into World Cup pages at build time. |

## Adding a new feature

1. Create a folder under `site/` (e.g. `site/basketball/`).
2. Add a requirements doc at the root (e.g. `requirements-basketball.md`).
3. Add a link from `site/index.html`.
4. Update this index.
