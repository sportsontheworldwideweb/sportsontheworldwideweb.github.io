# Requirements

## Overview

A tool for soccer fans to follow and compare how different continental confederations perform across FIFA World Cups — who's gaining rating ground, who's losing it, and how each tournament's results play out game by game. It does this by tracking ELO rating transfers between confederations as matches are played, across the 2018, 2022, and 2026 World Cups.

## Match List

#### Pages & navigation

- Each World Cup (2018, 2022, 2026) has its own page with its own URL (`2018.html`, `2022.html`, `2026.html`), so it can be linked/bookmarked directly.
- `index.html` is a minimal landing page with a short summary and links to each World Cup's page.
- Each World Cup page has simple navigation to switch between the three World Cup pages and back to the landing page.

#### Match list

The table has two groups of columns: **Game columns** and **Confederation columns**.

##### Game columns

- For the selected World Cup, list all games in chronological order.
- The game columns use a single header row: Date and # have their own header cells; Home and Away are super-headers spanning their respective columns; no sub-header row with individual column labels is shown.
- Column order, left to right:
  1. **Date** — no super-header; displayed in "Mon D" format (e.g. "Jun 2", "Jun 14", "Dec 12"), no year since the year is implied by the selected World Cup.
  2. **Game #** — no super-header; displayed as `#1`, `#2`, etc. The game number is the game's 1-based position in chronological order within that World Cup, stored in the data so it can be used as a stable identifier elsewhere (e.g. data entry).
  3. **[spacer]** — an empty column with no header, providing visual separation between the game identifiers and the Home/Away groups.
  4. **Home** super-header spanning: ELO, Flag, Score.
  5. **[score separator]** — a column displaying a literal `-` for every played game, visually joining the home and away scores (e.g. the row reads "3 - 1"). No super-header.
  6. **Away** super-header spanning: Score, Flag, ELO.
- The ELO column for each team combines pre-game ELO and delta into a single cell displayed as a concatenated string, e.g. `1873+4` or `1938-16`. When `eloChange` is null the cell is empty; when only `homeEloPre`/`awayEloPre` is null the pre-ELO portion is omitted and just the delta is shown.
- Each team is shown as its flag (an SVG image from `data/flags/`) only (no name), with the team's name shown on hover (e.g. via a tooltip).
- The table header row stays fixed/visible at the top of the viewport when scrolling down the match list.
- Each column is sized to fit its content — no fixed widths are set. If the table is wider than the viewport, it scrolls horizontally.

##### Row click — data entry panel

Each game row in the match list is clickable. Clicking a row expands an inline panel directly below that row (spanning the full table width). The panel has four lines:

1. The game label (e.g. "#7: Haiti vs Scotland").
2. Home score, away score, ELO magnitude (optional), and — only when both scores are filled in and equal (a draw) — a "Who gains ELO?" selector showing the two team names.
3. A "Generate command" button, a read-only copyable text field showing the resulting `scripts/set_result.py` command, and a "Copy" button. (See `## Data > ### Scripts` for the command format.)

All inputs are pre-filled with the game's existing values if already set. The "Who gains" selector is pre-selected based on the sign of the existing `eloChange`. Clicking the same row again (or clicking a different row) collapses the open panel. Only one panel is open at a time. There is no separate bottom-of-page widget.

##### Confederation panel (right side, toggleable)

The right side of the table is a panel of confederation columns that can be toggled between three views. The toggle is a segmented button control sitting above the panel in the header area, visually associated with the right panel only. Switching views must not cause the game columns on the left to shift or resize — the game section width is fixed regardless of which view is active. The transition between views is a simple instant swap (no animation required).

Only confederations with at least one team participating in the selected World Cup get a column in any view (e.g. if Oceania has no teams in the tournament, it has no column in any view). All confederation columns within a view have equal width.

**View 1 — ELO Shift (default)**

- One column per confederation showing its running cumulative ELO delta across games played so far.
- For each game, the home team's confederation gets `+eloChange` and the away team's confederation gets `-eloChange`. If both teams are in the same confederation, the net change is 0.
- Each cell shows the cumulative running total up to and including that row.
- Columns are ordered left-to-right by their final cumulative ELO total (highest first). This same ordering is used for both View 1 and View 2, so column positions do not shift when toggling between those two views.
- Cells are color-coded on a gradient: 0 is neutral (white), +400 is max green, -400 is max red, interpolated proportionally. Values beyond ±400 are clipped to the max color.
- For a game whose `eloChange` is `null`, cells are left empty and the running total does not advance.

**View 2 — W/D/L Record**

- One column per confederation showing its cumulative W/D/L record across games played so far, using the same column order as View 1 (by final cumulative ELO, highest first).
- Each cell displays three numbers in W-D-L order, formatted as e.g. `5-1-2` (wins-draws-losses), representing the running totals up to and including that row. No labels — the W/D/L order is implied by the view name.
- A win for a confederation is any game where a team from that confederation wins (outright, or on penalties). A loss is any game where a team from that confederation loses. A draw is any game that ends level after 90 minutes (regardless of penalty shootout outcome).
- If both teams are from the same confederation, the game counts as both a win and a loss for that confederation (one team won, one lost), or two draws in the case of a draw.
- For a game with `homeScore`/`awayScore` both `null`, the row's cells are empty and the running totals do not advance.

**View 3 — Competition Stats**

- Tournament-wide aggregate stats, not broken out by confederation — a fixed set of summary columns shown for the whole table.
- The total number of columns in View 3 must equal the number of confederation columns in Views 1 and 2, so the right panel stays the same total width across all three views. If there are N confederation columns, use N stat columns (padding with empty columns if N > 3, or merging if N < 3 — but in practice N is typically 5–6 so distribute the stats across N columns or group them sensibly).
- Core stats columns (always present):
  1. **Wins** — running count of decided games (games with a winner after 90 minutes).
  2. **Draws** — running count of drawn games (scores level after 90 minutes).
  3. **Win%** — running ratio of wins to total played games, displayed as a percentage (e.g. `62%`). A played game is any game where both scores are non-null.
- Remaining columns (to fill out to N total) are left blank (empty header, empty cells).
- Values accumulate row by row; unplayed games (`null` scores) leave the row empty and do not advance the totals.

## Tournament ELO Ranking Table

A standalone view — only one page view is visible at a time. The World Cup page has a segmented toggle that switches between **Match List** and **Rankings**; they never appear simultaneously. The navigation bar (links to other years) stays fixed regardless of which view is active. The Rankings view is only available for tournaments that have `teamElos` data (currently 2026 only; the toggle is omitted entirely from 2018 and 2022 pages).

Each view has its own URL via the hash fragment: `2026.html#matches` for the Match List and `2026.html#rankings` for the Rankings view. Switching views updates the hash; loading the page with a hash pre-selects that view. The default (no hash) is Match List.

#### Gamesets

A **gameset** is a named, ordered batch of consecutive games after which the ranking table adds a new snapshot column. Gamesets are defined per tournament by a fixed list of game-count boundaries. They are not stored in the game data — the boundaries are hardcoded per tournament and applied at render time.

For the 2026 World Cup the gamesets and their column labels are:

| Gameset | Column label | Description | Game count |
|---------|--------------|-------------|------------|
| 0 | Initial | Pre-tournament (starting `teamElos`) | — |
| 1 | Game 1 | Group stage, matchday 1 | 24 |
| 2 | Game 2 | Group stage, matchday 2 | 24 |
| 3 | Game 3 | Group stage, matchday 3 | 24 |
| 4 | 32 | Round of 32 | 16 |
| 5 | 16 | Round of 16 | 8 |
| 6 | 8 | Quarterfinals | 4 |
| 7 | 4 | Semifinals | 2 |
| 8 | Final | Third-place game + Final | 2 |

All 9 column headers are always shown. A column whose gameset is not yet complete shows empty cells — no flags, no ELO values.

#### Table structure

- **Rows** — one per rank position (1, 2, 3… up to the number of teams in `teamElos`). Each row represents a rank slot, not a fixed team.
- **Columns** — one per gameset, always all 9, in order left to right: Initial, Game 1, … Final.
- **Rank column** — a leftmost column showing the rank number (1, 2, 3…) for that row.
- **Column widths** — all snapshot columns (Initial through Final) have equal width. The rank column is narrower and sized to its content.

Each cell (row R, column C) shows the team currently occupying rank R in the snapshot for gameset C. As teams' ELOs shift between gamesets, the same team may appear in different rows across columns.

#### Cells

Each cell contains:
1. The team's **flag** (SVG from `data/flags/`).
2. The team's **ELO** at that snapshot (integer).

The team name is shown on hover (tooltip). Empty cells (gameset not yet complete) show nothing.

The Initial column uses each team's starting value from `teamElos`. Each subsequent column uses the team's ELO after all games in that gameset are applied.

#### Ranking and ties

Teams are ranked by ELO descending within each snapshot. Ties are broken by **stable sort**: if two teams have equal ELO, the one ranked higher in the previous snapshot remains ranked higher. This preserves relative order rather than arbitrarily reordering tied teams.

#### Eliminated teams

A team is considered **eliminated** as of the gameset after their last appearance in a game. Specifically: if a team played in gameset N but does not appear in any game in gameset N+1 or later, they are eliminated after gameset N. (For the group stage this naturally captures teams that don't qualify for the Round of 32; for knockout rounds it captures teams that lost.)

Eliminated teams remain in the rankings table — they are never removed. Their flag is rendered in greyscale to visually distinguish them from still-active teams.

#### Flag hover highlight

When the user hovers over any flag cell in the Rankings table, all flag cells in the table belonging to **other** teams are dimmed (reduced opacity). The hovered team's flag cells across all columns remain at full opacity. This makes it easy to visually trace a single team's ELO evolution across the full tournament. Leaving the table restores all flags to full opacity.


## Data

### Storage & delivery

- Match data is stored in separate data files (one per World Cup, e.g. `data/2018.json`), plus `data/teams.json`. These files are the source of truth.
- Pages open directly via `file://` with no server (per way-of-working.md), so they cannot `fetch` the data files at runtime. Instead, each World Cup page (`2018.html`, `2022.html`, `2026.html`) embeds the contents of its corresponding data file plus `data/teams.json` as JS constants.
- The embedded constants must be kept in sync with the data files and are clearly marked (e.g. a comment noting the source file) so it's obvious they are a copy, not hand-edited separately.

### Scripts

Entering the result of a played game is done via a command-line script, not the web UI and not by asking the AI to hand-edit files. The row-click panel in the match list (see `## Match List > ##### Row click`) generates the command for you.

- `scripts/set_result.py YEAR GAME_NUMBER HOME_SCORE AWAY_SCORE [ELO_CHANGE --gains {home|away}]` finds the game with that `gameNumber` in `data/YEAR.json`, sets its `homeScore`/`awayScore` (and `eloChange` if provided), then runs `build.py` to regenerate derived fields and embedded data.
- When supplying an ELO change, two things are required: the magnitude as a positive number, and which team gains it (`--gains home` or `--gains away`). The script applies the sign and stores the result.
- `scripts/set_result.py --list-teams` prints the index of every team's shorthand, full name, and confederation, sourced from `data/teams.json`.
- `scripts/build.py` computes `homeEloPre`/`awayEloPre` for every game (chaining `teamElos` starting ratings through prior results), then regenerates the embedded data in all three `*.html` pages. Run this after any manual edit to a data file.
- Both scripts are plain Python 3 with no dependencies and support `-h` / `--help`.

### Tournament data file structure

Each World Cup data file (`data/2018.json`, `data/2022.json`, `data/2026.json`) is a JSON object with two top-level keys:

- **`teamElos`** — an object mapping each participating team's name to its ELO rating at the start of the tournament. This is the source of truth for pre-tournament ratings; per-game pre-ELOs are derived from this by `build.py`.
- **`games`** — the ordered list of game records (see below).

`homeEloPre`/`awayEloPre` in each game record are **derived fields** computed by `build.py` and written back into the JSON. They must not be hand-edited; they will be overwritten on the next build.

For each team, `build.py` walks games in `gameNumber` order, tracking a running ELO that starts at `teamElos[team]`. For each game the team appears in, `homeEloPre`/`awayEloPre` is set to the running ELO at that point. After the game, if `eloChange` is non-null (game is played), the running ELO is updated. If `eloChange` is null (game not yet played), the chain stops — all subsequent games for that team get `null` pre-ELO, because the outcome of this game isn't known yet.

If a tournament JSON has no `teamElos` key (e.g. 2018, 2022), `build.py` leaves any existing `homeEloPre`/`awayEloPre` values in place and does not attempt to derive them.

### Game records

Each entry in the `games` array:

| Field | Type | Notes |
|-------|------|-------|
| gameNumber | number | 1-based, chronological order within the World Cup. Stable identifier used by `scripts/set_result.py`. |
| homeTeam | string | |
| homeScore | number \| null | `null` if not yet played. |
| awayTeam | string | |
| awayScore | number \| null | `null` if not yet played. |
| date | string (YYYY-MM-DD) \| null | `null` if not yet known. |
| eloChange | number \| null | ELO points transferred from away team to home team (positive = shift toward home team). `null` if not yet known. |
| homeEloPre | number \| null | Derived by `build.py`. Home team's ELO immediately before this game. `null` if the team has no entry in `teamElos`. |
| awayEloPre | number \| null | Derived by `build.py`. Away team's ELO immediately before this game. `null` if the team has no entry in `teamElos`. |

### Teams data

A single shared file `data/teams.json`, used across all World Cups.

| Field | Type | Notes |
|-------|------|-------|
| name | string | Must match team names used in game records |
| shorthand | string | FIFA 3-letter code, e.g. `BEL`. Used as a shorthand identifier in `scripts/set_result.py` |
| confederation | string | One of: Europe, Asia, Africa, South America, North America, Oceania |
| flag | string | [flag-icons](https://github.com/lipis/flag-icons) code for the team's flag (e.g. `be`), used to look up the SVG at `data/flags/<flag>.svg` |

To add a new team: add its row to `data/teams.json` with the appropriate flag-icons code, download the corresponding SVG from the [flag-icons 4x3 flags folder](https://github.com/lipis/flag-icons/tree/main/flags/4x3) into `data/flags/<flag>.svg`, then run `scripts/build.py`.

