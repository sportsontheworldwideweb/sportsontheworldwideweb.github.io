# Scale View Height Algorithm

## Why this exists

The Scale view positions flags proportionally to ELO on a vertical axis. When two teams have similar ELO ratings their flags occupy nearly the same vertical position, causing visual overlap. To resolve this, flags in a cluster are **dodged horizontally** — spread left/right around the column centerline.

The column width is fixed at `3 × flag_width + 2 × gap`, wide enough to hold exactly 3 flags side by side. This is the widest a column can be while still allowing all 9 gameset columns to fit on a screen without excessive horizontal scrolling. Going to 4 flags wide would require wider columns, breaking the consistent fixed-width layout across all views.

Therefore the hard constraint is: **depth must not exceed 3**. The axis height is the single free parameter that controls how spread-out ELO positions are in pixel space — a taller axis separates nearby ELOs more, reducing depth. The goal is to find the minimum height that satisfies the constraint.

---

## Constraints

1. **Depth ≤ 3** at every vertical point in any gameset column. (Depth 4 would require a 4th lane, overflowing the column width.)
2. **Axis height is minimized** subject to constraint 1. Minimum height keeps the view compact; a taller axis than necessary wastes screen space and makes the view harder to read.

---

## Definitions

**Flag height (`FLAG_PX_H`)** — the pixel height of one flag icon. Two flags visually overlap when the top of the lower flag is above the bottom of the upper flag, i.e. their top-to-top pixel distance is less than `FLAG_PX_H`.

**Depth** — the number of flags whose vertical intervals simultaneously overlap a single vertical point. Formally, at any Y coordinate, depth = number of flags whose `topPx ≤ Y < topPx + FLAG_PX_H`. The maximum depth across all Y positions within a gameset column is the column's depth for a given axis height.

**Axis height** — the pixel length of the ELO axis. A fixed pixel margin of `RANK_ROW_H / 2` is reserved at the top and bottom so the extreme flags align with rank 1 / rank N in the Rank view. Y position of a flag is computed as:

```
margin = RANK_ROW_H / 2
drawH  = height − 2 × margin − FLAG_PX_H
topPx  = margin + drawH × (1 − (elo − rawMin) / (rawMax − rawMin))
```

The flag's **top edge** sits at the ELO pixel position. `drawH` is reduced by `FLAG_PX_H` so the lowest-ranked flag's bottom stays within the bottom margin, keeping both ends inset symmetrically.

A taller axis stretches the ELO range into more pixels, increasing the distance between nearby teams and reducing cluster sizes.

---

## Algorithm

The minimum valid height is found by **binary search** over integer pixel values.

**Inputs:**
- All populated gameset snapshots (complete or live) with their team ELO values
- The axis ELO range `[rawMin, rawMax]` — the actual min/max ELO across all populated snapshots

**Steps:**

1. Check the error case: if any gameset column contains 4 or more teams with **identical ELO**, no finite height can separate them. Show a warning and return `MAX_H`.

2. Binary search over `[lo = 100, hi = MAX_H]`:
   - At each midpoint, compute the maximum depth across all gameset columns at that height.
   - If max depth ≥ 4: height is too small → raise `lo`.
   - If max depth ≤ 3: height may be reducible → lower `hi`.
   - Continue until `hi − lo ≤ 1`. Return `hi` (the smallest height that passes).

3. A single height is used for all gameset columns so they share the same vertical scale and remain visually aligned when reading across columns.

**Depth detection for a given height (sliding window):**

For each gameset snapshot:
1. Compute `topPx` for every team.
2. Sort `topPx` values ascending.
3. Two-pointer window: advance `hi` through the sorted list; advance `lo` whenever `tops[hi] − tops[lo] ≥ FLAG_PX_H`. The window size `hi − lo + 1` is the local depth.
4. The maximum window size across all positions and all snapshots is the max depth for this height.

---

## Horizontal dodge

After computing `topPx` positions, flags that overlap are fanned out into up to 3 horizontal lanes: left (`−STEP`), centre (`0`), right (`+STEP`), where `STEP = FLAG_PX_W + SCALE_GAP`.

Rendering is a two-pass process.

**Pass 1 — greedy lane assignment** (flags sorted by `topPx` ascending):

1. Maintain 3 lanes, each with a `nextFreeY` value (initialised to `−∞`).
2. For each flag, find all lanes where `nextFreeY ≤ topPx` (lane is free). Among those, pick the one with the **highest** `nextFreeY` (most recently used), so the emptiest lane is saved for future flags.
3. Assign the flag to lane index 0, 1, or 2; set `nextFreeY = topPx + FLAG_PX_H`.
4. If no lane is free (depth > 3 — should not occur at the computed minimum height), fall back to centre (lane 1).

This greedy approach correctly handles non-transitive overlaps: a flag that only overlaps its immediate neighbour can reuse a lane freed by an earlier flag.

**Pass 2 — visual centering** (transitive cluster grouping):

After lane assignment, flags are grouped into transitive visual clusters: a consecutive run of flags where each flag's `topPx` is within `FLAG_PX_H` of the previous one. Within each cluster:

1. Collect the distinct lane indices used by the cluster. The number of distinct lanes determines the spread: `spread = (count − 1) × STEP`.
2. Sort those lanes by the **minimum `topPx`** of all flags in that lane (i.e. the highest-ELO flag in each lane). Assign offsets left-to-right in that sorted order: k-th lane gets `−spread/2 + k × STEP`.
3. Apply each flag's lane offset via `left: calc(50% + Xpx)`.

This ensures the lane containing the highest-ELO flag always gets the leftmost offset. Isolated flags land at 0, pairs are symmetric at ±`STEP/2`, full clusters span `[−STEP, 0, +STEP]`.

**Why sort lanes by min topPx, not by lane index:**
Pass 1's greedy algorithm assigns lane indices based on packing order, not ELO rank — so a higher-ELO flag can end up in lane 1 and a lower-ELO flag in lane 0. Sorting lanes by their topmost flag's position decouples the visual left/right assignment from the arbitrary packing numbering.

**Shared-lane case:** Two flags can share a lane when the upper flag ends (its `topPx + FLAG_PX_H`) before the lower flag begins. In that case both get the same horizontal offset (same lane, same column) with no visual overlap. The spread is still computed from distinct lane count, so a 3-flag cluster using only 2 lanes stays as a 2-wide pair — not incorrectly expanded to 3 positions.

---

## Implementation

**Constants** (in `2026.html`):
| Constant | Value | Meaning |
|----------|-------|---------|
| `FLAG_PX_W` | 35 | Flag icon width in px (border drawn inside via `box-sizing: border-box`) |
| `FLAG_PX_H` | 24 | Flag icon height in px (border drawn inside via `box-sizing: border-box`) |
| `SCALE_GAP` | 3 | Px between side-by-side flags in a cluster |
| `MAX_H` | 80000 | Binary search upper bound / error-case fallback |
| `lo` (binary search) | 100 | Safe lower bound — always has 4+ clusters at this height given the number of teams |

**Functions** (in `2026.html`):
- `scaleTopPx(elo, scaleMin, scaleMax, height)` — converts an ELO to a pixel Y position. Return value is **rounded to the nearest integer**. This is essential: floating-point arithmetic can produce results like `1188.0000000000002` instead of `1188`, making a gap of exactly `FLAG_PX_H` appear as `23.9999...`. Without rounding, the transitive cluster grouping in Pass 2 incorrectly chains flags that are visually touching-but-not-overlapping into the same cluster, producing unexpected horizontal offsets. Rounding ensures all gap comparisons against `FLAG_PX_H` behave as intended.
- `maxClusterSizeForHeight(snapshots, ranked, scaleMin, scaleMax, height)` — returns the max depth (sliding window) across all snapshots at a given height.
- `computeScaleHeight(snapshots, ranked, scaleMin, scaleMax)` — runs the binary search; returns `{ height, hasError }`.
