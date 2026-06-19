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

## Tournament ELO Rankings

A standalone view — only one page view is visible at a time. The World Cup page has a segmented toggle that switches between **Match List** and **Rankings**; they never appear simultaneously. The navigation bar (links to other years) stays fixed regardless of which view is active. The Rankings view is only available for tournaments that have `teamElos` data (currently 2026 only; the toggle is omitted entirely from 2018 and 2022 pages).

Each view has its own URL via the hash fragment: `2026.html#matches` for the Match List and `2026.html#rankings` for the Rankings view. Switching views updates the hash; loading the page with a hash pre-selects that view. The default (no hash) is Match List.

#### Gamesets

A **gameset** is a batch of games in which each active team plays at most once — it is one "turn" for every team still in the tournament. Gamesets are defined per tournament by a fixed list of game-count boundaries, applied in chronological order. They are not stored in the game data — the boundaries are hardcoded per tournament and applied at render time. A gameset is complete when every team that has a game in its range has a recorded result; teams with no game in the range (already eliminated, or byes) do not count toward completion.

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

All 9 gameset columns are always shown. The Rankings view has a segmented toggle that switches between **Rank** and **Scale** views of the same gameset data. The toggle sits above the ranking area. Switching between Rank and Scale must not shift the gameset column positions — the horizontal layout is identical in both views.

#### Ranking and ties

Teams are ranked by ELO descending within each gameset snapshot. Ties are broken by **stable sort**: if two teams have equal ELO, the one ranked higher in the previous snapshot remains ranked higher.

#### Live gameset

At any point in the tournament there is exactly one **live gameset column**: the in-progress gameset if any games in its range have been played but it is not yet complete, or the next gameset if the most recent gameset just completed and the next hasn't started.

The live gameset column is always shown populated — it is never empty:

- It is seeded from the previous gameset's final ELOs (or from `teamElos` if it is the first gameset).
- As results come in, the column updates: each team's ELO and rank reflects all results recorded so far within the live gameset.
- Teams are always ranked by their current ELO, including mid-gameset. There is no hold on unplayed teams — the live standings shift with every result entered.

Teams that have a game scheduled in the live gameset's range but no result recorded yet are shown with a **"hasn't played" visual**: a muted grey distinct from the greyscale used for eliminated teams. Once their game result is entered, they revert to normal styling.

Only the live gameset column uses this treatment. Completed gameset columns always show final ELOs with no "hasn't played" styling. Future gameset columns (beyond the live one) show nothing.

#### Eliminated teams

A team is considered **eliminated** as of the gameset after their last appearance in a game. Specifically: if a team played in gameset N but does not appear in any game in gameset N+1 or later, they are eliminated after gameset N. (For the group stage this naturally captures teams that don't qualify for the Round of 32; for knockout rounds it captures teams that lost.)

Eliminated teams remain in both views — they are never removed. Their flag is rendered in greyscale to visually distinguish them from active teams.

#### Rankings shared layout

Both Rank and Scale views share the same canvas structure: one vertical column per gameset, all columns equal width, with a leftmost axis column. Toggling between views causes no horizontal shift.

- *Flag dimensions*: each flag icon has a fixed pixel width and height, consistent across both views.
- *Column width*: every gameset column has a fixed minimum width of `3 × flag_width + 2 × gap` (where *gap* is a fixed small spacing between side-by-side flags, defined in the Scale view). This applies uniformly across both views. Column separator lines are always fully visible; no flag extends past its column boundary. (The `3 ×` derives from the Scale view cluster constraint — see `scale-algorithm.md`.)

---

#### Flag info panel

Hovering any flag in the Rankings view populates a fixed side panel that sits to the left of the rankings grid, vertically centered on the viewport. The panel never overlaps the grid or its flags.

The panel always shows the same set of fields in the same order, so its height never changes while browsing:

| Field | Content |
|-------|---------|
| Flag | The team's flag image (large) |
| Name | Team name (bold) |
| ELO | ELO at that gameset snapshot |
| *(divider)* | |
| Date | Game date in "Mon D" format (e.g. "Jun 15"), or — if no game |
| Opponent | Opposing team name, or — |
| Score | Score from the hovered team's perspective (their goals first), or — |
| ELO Δ | ELO change, green for gain, red for loss, or — |

When there is no game in the column (Initial snapshot, or a team with no game scheduled in that gameset), the bottom four fields show —. For a pending game (live column, result not yet entered), Date and Opponent are shown but Score and ELO Δ show —.

**Behaviour:**
- The panel appears immediately when the cursor first lands on a flag.
- Moving between flags updates the panel content instantly with no flicker — the panel stays visible throughout.
- The panel hides 300 ms after the cursor leaves the rankings area entirely (same grace period as the highlight).

---

#### Flag hover highlight

When the user hovers over any flag in the Rankings view, all flags belonging to **other** teams are dimmed (reduced opacity). The hovered team's flags across all gameset columns remain at full opacity, making it easy to trace a single team's ELO evolution across the tournament. The hovered team's flags are also brought to the front (highest z-index) so they are never obscured by overlapping flags.

The highlight uses debounced activation and deactivation to avoid flicker:
- **Activate delay (200 ms):** the highlight only appears after the cursor has rested on a flag for 200 ms. Brief passes don't trigger it.
- **Deactivate grace period (300 ms):** when the cursor moves to empty space or leaves the rankings area, the highlight holds for 300 ms before clearing. This prevents flicker when crossing flag edges.
- **Instant cancel:** if the cursor returns to the already-highlighted team's flag during the grace period, the deactivation is cancelled immediately with no re-delay.

---

#### Rank view

Flags are **evenly spaced** — each rank position occupies the same vertical height regardless of ELO magnitude. This is a positional ranking, not a proportional one.

Each flag occupies its rank slot for that gameset snapshot: rank 1 at the top, rank N at the bottom. A leftmost axis column shows rank numbers (1, 2, 3…) aligned to each rank slot. No ELO number is shown alongside the flag. Hovering a flag shows the info panel — see *Flag info panel* above.

A dotted horizontal line is drawn between every 4th and 5th rank (i.e. after ranks 4, 8, 12, …), spanning all columns, behind the flags.

---

#### Scale view

Flags are **positioned proportionally to ELO** — a team's vertical position on the axis directly encodes its ELO value. Y position is never altered for any reason. The gameset column X-positions are identical to Rank view so toggling between the two causes no horizontal shift.

**Definitions (Scale view)**
- *Gap*: a fixed small spacing (a few pixels) between flags placed side by side.
- *Depth*: at any vertical point on the axis, the number of flags whose pixel intervals simultaneously cover that point. Two flags overlap when their top-to-top pixel distance is less than one flag height.

**Axis range**
The ELO axis spans from the lowest to the highest ELO of any team across all populated gameset snapshots. A flag's **top edge** sits at its ELO pixel position — not the center. This means a team rated 1998 reads as "just below 2000," matching the natural interpretation that a flag hangs down from its rating. Centering would make the team appear to straddle the line above, which is misleading.

A fixed pixel margin of `RANK_ROW_H / 2` is applied at the top and at the bottom (below the lowest flag's bottom edge), keeping the extreme flags inset from the axis ends symmetrically.

Note: the Scale view's vertical positioning is **independent of the Rank view** — only the horizontal column layout is shared. The Rank view spaces flags evenly by rank; the Scale view spaces them proportionally by ELO. Toggling between views changes flag vertical positions but not column positions.

**Axis height**
No visual overlap between flags is allowed. The axis height is the **minimum height at which the maximum depth across all gameset columns is ≤ 3** — ensuring every point on the axis is covered by at most 3 flags, which is the column's horizontal dodge capacity. A single height is computed across all gameset columns together so all columns share the same vertical scale and remain aligned. See `scale-algorithm.md` for the constraints, algorithm, and implementation.

Error case: if 4 or more teams share an identical ELO in the same gameset column, no axis height can resolve the cluster. A visible warning is shown in that column and the smallest achievable height is used.

**Y-axis tick marks**
The tick interval (ELO units between marks) is selected from `[200, 100, 50, 25, 10, 5, 2]`, largest first, choosing the first value whose pixel spacing falls between 150 px and 300 px. If no candidate falls in that range (e.g. the axis is extremely compressed or stretched), the candidate whose spacing is closest to 200 px is used as a fallback. Tick labels are shown at every multiple of the chosen interval within the axis range, once in the leftmost axis column. A dotted horizontal line is drawn at each tick, spanning all columns, behind the flags.

**Horizontal dodge**
Overlapping flags are placed side by side using a two-pass approach. Y positions are never altered.

*Pass 1 — greedy lane assignment:* flags are sorted by Y position and assigned to one of 3 abstract lanes (0, 1, 2). Each flag takes the lane that is currently free and has been used most recently, leaving the emptiest lane available for future flags. This correctly handles non-transitive overlaps: a flag that only overlaps its immediate neighbour can reuse a lane freed by an earlier flag.

*Pass 2 — visual centering:* flags are grouped into transitive visual clusters (consecutive flags sorted by Y that each overlap the next). Within each cluster, the lane indices actually used are mapped to pixel offsets centered on the column midline: a cluster using 1 lane gets offset 0; 2 lanes get ±`(gap+flag_width)/2`; 3 lanes get `−(flag_width+gap)`, `0`, `+(flag_width+gap)`. This keeps isolated flags centered and small clusters symmetric regardless of which abstract lanes the greedy pass assigned.

**Flag display**
No ELO number is shown alongside the flag. Hovering a flag shows the info panel — see *Flag info panel* above. Z-index is determined by rank: higher-ranked teams (lower rank number) render on top.

---

## Debug

Debug features are toggled via UI controls that are always visible but clearly labelled as debug. They are off by default and have no effect on normal rendering.

**Show binding clusters** (Scale view only) — a checkbox labelled "debug: show binding clusters". When checked, a red outline is drawn around each depth-4 window that would appear if the axis were 1 pixel shorter — i.e. each set of flags whose vertical intervals would all overlap a common point at `scaleH − 1`. These are the flags forcing the axis to be as tall as it is: at the computed minimum height their depth is ≤ 3, but one pixel shorter it would reach 4 and overflow the column. Off by default.


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

