#!/usr/bin/env python3
"""Regenerate 2018.html / 2022.html / 2026.html from data/*.json and the
page template defined in this file.

Run this after editing any data/*.json file by hand, or use
scripts/set_result.py for a one-line score update.

For tournament files that include a top-level "teamElos" key, homeEloPre and
awayEloPre are derived automatically and written back to the JSON before the
HTML is regenerated.

The three HTML files are pure build artifacts — edit the template here, not
the HTML files directly.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YEARS = [1998, 2002, 2006, 2010, 2014, 2018, 2022, 2026]

# Per-year static configuration: gameset boundaries and the comment that
# describes the tournament format. These are the only parts of the page that
# differ by year beyond the data blocks.
PER_YEAR_CONFIG = {
    1998: {
        'gamesets_comment': '// Gameset boundaries: [label, lastGameNumber]. 32-team format: 3 group-stage matchdays + knockout.',
        'gamesets': [
            ('Initial',  0),
            ('MD1',     16),
            ('MD2',     32),
            ('MD3',     48),
            ('16',      56),
            ('8',       60),
            ('4',       62),
            ('Final',   64),
        ],
    },
    2002: {
        'gamesets_comment': '// Gameset boundaries: [label, lastGameNumber]. 32-team format: 3 group-stage matchdays + knockout.',
        'gamesets': [
            ('Initial',  0),
            ('MD1',     16),
            ('MD2',     32),
            ('MD3',     48),
            ('16',      56),
            ('8',       60),
            ('4',       62),
            ('Final',   64),
        ],
    },
    2006: {
        'gamesets_comment': '// Gameset boundaries: [label, lastGameNumber]. 32-team format: 3 group-stage matchdays + knockout.',
        'gamesets': [
            ('Initial',  0),
            ('MD1',     16),
            ('MD2',     32),
            ('MD3',     48),
            ('16',      56),
            ('8',       60),
            ('4',       62),
            ('Final',   64),
        ],
    },
    2010: {
        'gamesets_comment': '// Gameset boundaries: [label, lastGameNumber]. 32-team format: 3 group-stage matchdays + knockout.',
        'gamesets': [
            ('Initial',  0),
            ('MD1',     16),
            ('MD2',     32),
            ('MD3',     48),
            ('16',      56),
            ('8',       60),
            ('4',       62),
            ('Final',   64),
        ],
    },
    2014: {
        'gamesets_comment': '// Gameset boundaries: [label, lastGameNumber]. 32-team format: 3 group-stage matchdays + knockout.',
        'gamesets': [
            ('Initial',  0),
            ('MD1',     16),
            ('MD2',     32),
            ('MD3',     48),
            ('16',      56),
            ('8',       60),
            ('4',       62),
            ('Final',   64),
        ],
    },
    2018: {
        'gamesets_comment': '// Gameset boundaries: [label, lastGameNumber]. 32-team format: 3 group-stage matchdays + knockout.',
        'gamesets': [
            ('Initial',  0),
            ('MD1',     16),
            ('MD2',     32),
            ('MD3',     48),
            ('16',      56),
            ('8',       60),
            ('4',       62),
            ('Final',   64),
        ],
    },
    2022: {
        'gamesets_comment': '// Gameset boundaries: [label, lastGameNumber]. 32-team format: 3 group-stage matchdays + knockout.',
        'gamesets': [
            ('Initial',  0),
            ('MD1',     16),
            ('MD2',     32),
            ('MD3',     48),
            ('16',      56),
            ('8',       60),
            ('4',       62),
            ('Final',   64),
        ],
    },
    2026: {
        'gamesets_comment': '// Gameset boundaries: [label, lastGameNumber]. lastGameNumber=0 means pre-tournament.',
        'gamesets': [
            ('Initial',  0),
            ('Game 1',  24),
            ('Game 2',  48),
            ('Game 3',  72),
            ('32',      88),
            ('16',      96),
            ('8',      100),
            ('4',      102),
            ('Final',  104),
        ],
    },
}

CONFEDERATIONS = ["Europe", "Asia", "Africa", "South America", "North America", "Oceania"]


def load(name):
    return json.load(open(ROOT / "data" / name))


def derive_elos(data):
    """Compute homeEloPre/awayEloPre for all games in-place from teamElos.

    Returns the games list. If data has no teamElos, games are returned
    unchanged (existing homeEloPre/awayEloPre values are preserved).
    """
    if isinstance(data, list) or "teamElos" not in data:
        return data if isinstance(data, list) else data["games"]

    current = dict(data["teamElos"])
    broken = set()  # teams whose ELO chain has hit an unplayed game

    for game in data["games"]:
        home = game["homeTeam"]
        away = game["awayTeam"]

        game["homeEloPre"] = current[home] if home in current and home not in broken else None
        game["awayEloPre"] = current[away] if away in current and away not in broken else None

        if game.get("eloChange") is not None:
            # eloChange sign convention: positive = home gained, negative = away gained.
            delta = game["eloChange"]
            if home in current and home not in broken:
                current[home] += delta
            if away in current and away not in broken:
                current[away] -= delta
        else:
            broken.add(home)
            broken.add(away)

    return data["games"]


def validate(data, year, team_names):
    """Validate a tournament data file. Raises ValueError on the first problem found."""
    if not isinstance(data, dict):
        raise ValueError(f"{year}.json: top-level value must be a JSON object, got {type(data).__name__}")
    if "games" not in data:
        raise ValueError(f"{year}.json: missing required key 'games'")

    games = data["games"]
    if not isinstance(games, list):
        raise ValueError(f"{year}.json: 'games' must be an array")

    seen_numbers = {}
    for i, g in enumerate(games):
        ctx = f"{year}.json game #{g.get('gameNumber', f'[index {i}]')}"

        # Required fields present
        for field in ("gameNumber", "homeTeam", "awayTeam", "date"):
            if field not in g:
                raise ValueError(f"{ctx}: missing required field '{field}'")

        # gameNumber must be a positive integer
        gn = g["gameNumber"]
        if not isinstance(gn, int) or gn < 1:
            raise ValueError(f"{ctx}: 'gameNumber' must be a positive integer, got {gn!r}")
        if gn in seen_numbers:
            raise ValueError(f"{ctx}: duplicate gameNumber {gn} (first seen at index {seen_numbers[gn]})")
        seen_numbers[gn] = i

        # Team names must exist in teams.json
        for side in ("homeTeam", "awayTeam"):
            name = g.get(side)
            if name not in team_names:
                raise ValueError(f"{ctx}: {side} '{name}' not found in data/teams.json")

        # Scores must be non-negative integers or null
        for side in ("homeScore", "awayScore"):
            v = g.get(side)
            if v is not None and (not isinstance(v, int) or v < 0):
                raise ValueError(f"{ctx}: '{side}' must be a non-negative integer or null, got {v!r}")

        # eloChange must be an integer or null
        ec = g.get("eloChange")
        if ec is not None and not isinstance(ec, int):
            raise ValueError(f"{ctx}: 'eloChange' must be an integer or null, got {ec!r}")

        # eloChange sign must match the score result (fix #8)
        hs = g.get("homeScore")
        as_ = g.get("awayScore")
        if ec is not None and hs is not None and as_ is not None:
            if hs > as_ and ec < 0:
                raise ValueError(
                    f"{ctx}: eloChange={ec} is negative but home team won ({hs}–{as_}). "
                    f"Positive = home gained; negative = away gained."
                )
            if as_ > hs and ec > 0:
                raise ValueError(
                    f"{ctx}: eloChange={ec} is positive but away team won ({as_}–{hs}). "
                    f"Positive = home gained; negative = away gained."
                )

    # gameNumbers must be contiguous from 1
    if seen_numbers:
        actual = sorted(seen_numbers)
        expected = list(range(1, len(actual) + 1))
        if actual != expected:
            missing = sorted(set(expected) - set(actual))
            raise ValueError(f"{year}.json: game numbers are not contiguous from 1; missing: {missing}")


def build_nav(current_year):
    parts = []
    for y in YEARS:
        parts.append(f'<strong>{y}</strong>' if y == current_year else f'<a href="{y}.html">{y}</a>')
    parts.append('<a href="history.html">History</a>' if current_year != 'history' else '<strong>History</strong>')
    parts.append('<a href="../../index.html">Home</a>')
    return '<nav>' + ' | '.join(parts) + '</nav>'


def flag_rotation(team_name):
    """Deterministic flag tilt matching the JS flagRotation() function."""
    h = 0
    for ch in team_name:
        h = (h * 31 + ord(ch)) & 0xffff
    return ((h % 21) - 10) * 0.1


def build_history_page(shared_css):
    """Generate the year-over-year knockout round comparison page.

    For each year, three rows are rendered:
      F4  — 4 semi-finalists, ELO entering SFs, ranked by ELO
      F8  — all 8 QF entrants, ELO entering QFs, ranked by ELO
      F16 — all 16 R16 entrants, ELO entering R16, ranked by ELO

    Teams appear in multiple rows (once per round they played).
    """
    # (r16_range, qf_range, sf_range) — inclusive game-number ranges per year
    ROUND_RANGES = {
        # 32-team format: R16=49-56, QF=57-60, SF=61-62
        1998: (range(49, 57), range(57, 61), range(61, 63)),
        2002: (range(49, 57), range(57, 61), range(61, 63)),
        2006: (range(49, 57), range(57, 61), range(61, 63)),
        2010: (range(49, 57), range(57, 61), range(61, 63)),
        2014: (range(49, 57), range(57, 61), range(61, 63)),
        2018: (range(49, 57), range(57, 61), range(61, 63)),
        2022: (range(49, 57), range(57, 61), range(61, 63)),
        # 48-team format: R16=89-96, QF=97-100, SF=101-102
        2026: (range(89, 97), range(97, 101), range(101, 103)),
    }

    teams_by_name = {t['name']: t for t in load('teams.json')}

    def team_info(name, elo):
        t = teams_by_name.get(name, {})
        return {'name': name, 'flag': t.get('flag', ''), 'elo': elo}

    def round_participants(games_by_num, game_range):
        """Return dict of {team_name: team_info} for all teams in the given games."""
        result = {}
        for gn in game_range:
            g = games_by_num.get(gn)
            if g is None:
                continue
            result[g['homeTeam']] = team_info(g['homeTeam'], g.get('homeEloPre'))
            result[g['awayTeam']] = team_info(g['awayTeam'], g.get('awayEloPre'))
        return result

    year_data = []
    for year in reversed(YEARS):
        data_path = ROOT / 'data' / f'{year}.json'
        if not data_path.exists():
            continue
        data = json.load(open(data_path))
        games = derive_elos(data)
        games_by_num = {g['gameNumber']: g for g in games}

        r16_range, qf_range, sf_range = ROUND_RANGES[year]

        # Participants dict per round: {name: team_info}
        r16 = round_participants(games_by_num, r16_range)
        qf  = round_participants(games_by_num, qf_range)
        sf  = round_participants(games_by_num, sf_range)

        # F4: all 4 SF entrants, ELO entering SFs
        # F8: all 8 QF entrants, ELO entering QFs (includes those who advanced)
        # F16: all 16 R16 entrants, ELO entering R16 (includes those who advanced)
        f4  = sorted(sf.values(),  key=lambda x: x['elo'] or 0, reverse=True)
        f8  = sorted(qf.values(),  key=lambda x: x['elo'] or 0, reverse=True)
        f16 = sorted(r16.values(), key=lambda x: x['elo'] or 0, reverse=True)

        has_sf = bool(sf)
        has_qf = bool(qf)
        has_r16 = bool(r16)

        year_data.append({
            'year': year,
            'f4': f4 if has_sf else None,
            'f8': f8 if has_qf else None,
            'f16': f16 if has_r16 else None,
        })

    nav = build_nav('history')

    def flag_cell(team):
        flag = team['flag']
        name = team['name']
        elo = team['elo']
        rot = flag_rotation(name)
        elo_str = str(elo) if elo is not None else '—'
        safe_name = name.replace('"', '&quot;')
        icon = (f'<span class="icon" style="background-image:url(\'flags/{flag}.svg\');'
                f'transform:rotate({rot}deg)" title="{safe_name}"></span>') if flag else name
        return (f'<td class="hist-cell" data-team="{safe_name}">'
                f'<div class="hist-inner">{icon}'
                f'<span class="hist-elo">{elo_str}</span></div></td>')

    def empty_cells(n):
        return ''.join('<td class="hist-cell"></td>' for _ in range(n))

    def pending_cell(colspan, msg='Not yet played'):
        return f'<td colspan="{colspan}" class="hist-pending">{msg}</td>'

    # All rows left-align: F4=4 cols, F8=8 cols, F16=16 cols, all starting at col 1.
    # The table has 16 data columns total; shorter rows leave trailing empties.
    # Year cell is duplicated in all three rows; CSS controls which one is visible
    # so the year always appears next to the topmost visible row in each group.
    MAX_COLS = 16
    body_rows = ''
    for yd in year_data:
        year = yd['year']
        f4, f8, f16 = yd['f4'], yd['f8'], yd['f16']

        # F4 row
        body_rows += f'<tr class="hist-group-top row-f4"><th class="year-cell year-f4">{year}</th>'
        body_rows += '<td class="round-label">F4</td>'
        if f4:
            body_rows += ''.join(flag_cell(t) for t in f4)
            body_rows += empty_cells(MAX_COLS - len(f4))
        else:
            body_rows += pending_cell(MAX_COLS)
        body_rows += '</tr>\n'

        # F8 row
        body_rows += f'<tr class="row-f8"><th class="year-cell year-f8">{year}</th>'
        body_rows += '<td class="round-label">F8</td>'
        if f8:
            body_rows += ''.join(flag_cell(t) for t in f8)
            body_rows += empty_cells(MAX_COLS - len(f8))
        else:
            body_rows += pending_cell(MAX_COLS)
        body_rows += '</tr>\n'

        # F16 row
        body_rows += f'<tr class="hist-group-bottom row-f16"><th class="year-cell year-f16">{year}</th>'
        body_rows += '<td class="round-label">F16</td>'
        if f16:
            body_rows += ''.join(flag_cell(t) for t in f16)
            body_rows += empty_cells(MAX_COLS - len(f16))
        else:
            body_rows += pending_cell(MAX_COLS)
        body_rows += '</tr>\n'

    # 16 uniform data columns
    col_headers = ''.join('<th class="col-data"></th>' for _ in range(MAX_COLS))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World Cup ELO - History</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Fredoka+One&display=swap" rel="stylesheet">
<style>
{shared_css}
.year-cell {{
  font-family: 'Permanent Marker', cursive;
  font-size: 1.1rem;
  padding: 0.4rem 1rem 0.4rem 0.4rem;
  vertical-align: middle;
  white-space: nowrap;
  border-bottom: none;
}}
.round-label {{
  font-family: 'Permanent Marker', cursive;
  font-size: 0.8rem;
  color: #888;
  padding: 0.2rem 0.5rem;
  white-space: nowrap;
  border-bottom: none;
  vertical-align: middle;
}}
.hist-cell {{
  text-align: center;
  padding: 0.25rem 0.3rem;
  border-bottom: none;
  vertical-align: middle;
  min-width: 2.6rem;
}}
.hist-inner {{
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}}
.hist-cell .icon {{
  display: block;
  width: 2.2em;
  height: 1.5em;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  border: 1px solid #ccc;
  filter: saturate(0.8);
}}
.hist-elo {{
  font-size: 0.68rem;
  color: #555;
  line-height: 1;
}}
.hist-pending {{
  color: #bbb;
  font-style: italic;
  font-size: 0.8rem;
  vertical-align: middle;
  border-bottom: none;
}}
.hist-group-top td, .hist-group-top th {{ border-top: 2px solid #C0392B; }}
.hist-group-bottom td, .hist-group-bottom th {{ border-bottom: 2px solid #C0392B; }}
.col-data {{ background: #C0392B; min-width: 2.6rem; }}
thead th {{ border-bottom: none; }}
/* Row visibility toggles */
table.hide-f4  tr.row-f4  {{ display: none; }}
table.hide-f8  tr.row-f8  {{ display: none; }}
table.hide-f16 tr.row-f16 {{ display: none; }}
/* Year cell: show only in the topmost visible row of each group.
   Default: F4 shows, F8 and F16 hide. */
.year-f8, .year-f16 {{ display: none; }}
/* F4 hidden → F8 shows year */
table.hide-f4 .year-f8 {{ display: table-cell; }}
/* F4+F8 hidden → F16 shows year; F4 hidden alone keeps F8 visible */
table.hide-f4.hide-f8 .year-f8  {{ display: none; }}
table.hide-f4.hide-f8 .year-f16 {{ display: table-cell; }}
/* Hover: dim all cells except the hovered team */
table.dimming .hist-cell[data-team] {{ opacity: 0.15; transition: opacity 0.1s; }}
table.dimming .hist-cell.team-highlight {{ opacity: 1; }}
</style>
</head>
<body>
{nav}
<h1>World Cup History</h1>
<p style="color:#555;margin-top:-0.5rem">Final 4 / 8 / 16 for each tournament, ranked by ELO entering that round.</p>

<div class="view-toggle" style="margin-bottom:1rem">
  <button id="btn-f4"  class="active" onclick="toggleRound('f4')">F4</button>
  <button id="btn-f8"  class="active" onclick="toggleRound('f8')">F8</button>
  <button id="btn-f16" class="active" onclick="toggleRound('f16')">F16</button>
</div>

<div class="table-wrap">
<table id="hist-table">
  <thead>
    <tr>
      <th>Year</th>
      <th></th>
      {col_headers}
    </tr>
  </thead>
  <tbody>
{body_rows}  </tbody>
</table>
</div>

<script>
function toggleRound(round) {{
  const table = document.getElementById('hist-table');
  const btn = document.getElementById('btn-' + round);
  const hidden = table.classList.toggle('hide-' + round);
  btn.classList.toggle('active', !hidden);
}}

(function() {{
  const table = document.getElementById('hist-table');
  const cells = Array.from(table.querySelectorAll('.hist-cell[data-team]'));

  cells.forEach(function(cell) {{
    cell.addEventListener('mouseenter', function() {{
      const team = cell.dataset.team;
      table.classList.add('dimming');
      cells.forEach(function(c) {{
        if (c.dataset.team === team) c.classList.add('team-highlight');
      }});
    }});
    cell.addEventListener('mouseleave', function() {{
      table.classList.remove('dimming');
      cells.forEach(function(c) {{ c.classList.remove('team-highlight'); }});
    }});
  }});
}})();
</script>

</body>
</html>
"""


def format_gamesets_js(gamesets):
    """Format a list of (label, lastGameNumber) pairs as a JS array literal."""
    max_label_len = max(len(label) for label, _ in gamesets)
    lines = ['[']
    for label, last_gn in gamesets:
        padding = ' ' * (max_label_len - len(label))
        lines.append(f"  ['{label}',{padding} {last_gn:3d}],")
    lines[-1] = lines[-1].rstrip(',')  # no trailing comma on last entry
    lines.append(']')
    return '\n'.join(lines)


def build_script_block(year, games_js, teams_js, team_elos_js, config):
    conf_js = json.dumps(CONFEDERATIONS)
    gamesets_comment = config['gamesets_comment']
    gamesets_js = format_gamesets_js(config['gamesets'])

    parts = [
        f'// BEGIN:games{year}',
        games_js,
        f'// END:games{year}',
        '',
        '// BEGIN:teams',
        teams_js,
        '// END:teams',
    ]

    if team_elos_js:
        parts += [
            '',
            f'// BEGIN:teamElos{year}',
            team_elos_js,
            f'// END:teamElos{year}',
            '',
        ]
    else:
        parts.append('')

    parts += [
        f'const GAMES = games{year};',
        f'const YEAR = {year};',
        f'const TEAM_ELOS = teamElos{year};' if team_elos_js else 'const TEAM_ELOS = {};',
        f'const CONFEDERATIONS = {conf_js};',
        gamesets_comment,
        f'const GAMESETS = {gamesets_js};',
        "const tbody = document.getElementById('games');",
        "const thead = document.querySelector('#matches-view thead');",
    ]

    return '\n'.join(parts)


def page_html(year, script_block, shared_css, shared_js):
    nav = build_nav(year)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World Cup ELO - {year}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Fredoka+One&display=swap" rel="stylesheet">
<style>
{shared_css}
</style>
</head>
<body>
{nav}
<h1>World Cup ELO - {year}</h1>

<div style="display:flex; align-items:center; gap:1rem; flex-wrap:wrap;">
  <div class="page-toggle view-toggle">
    <button id="tab-matches" class="active" onclick="setPageView('matches')">Match List</button>
    <button id="tab-rankings" onclick="setPageView('rankings')">Rankings</button>
  </div>
  <button id="btn-data-entry" onclick="toggleDataEntry()" style="font-family:'Permanent Marker',cursive; font-size:0.75rem; background:transparent; border:1px dashed #aaa; border-radius:4px; padding:0.2rem 0.7rem; cursor:pointer; color:#888;">Data Entry</button>
</div>

<div id="matches-view">
  <table>
    <thead></thead>
    <tbody id="games"></tbody>
  </table>
</div>

<div id="rankings-view">
  <div class="rankings-toggle view-toggle">
    <button id="tab-rank" class="active" onclick="setRankView('rank')">Rank</button>
    <button id="tab-scale" onclick="setRankView('scale')">Scale</button>
  </div>
  <div class="rankings-filter-controls">
    <label><input type="checkbox" id="chk-show-elim" onchange="toggleShowEliminated()"> Show eliminated</label>
    <label id="true-rank-label" style="opacity:1"><input type="checkbox" id="chk-true-rank" onchange="toggleTrueRank()"> True rank</label>
  </div>
  <label style="font-size:0.75rem;color:#c00;margin-left:1rem;user-select:none">
    <input type="checkbox" id="debug-clusters" onchange="renderRankings()"> debug: show binding clusters
  </label>
  <div id="rankings-outer">
    <div id="rank-info"></div>
    <div class="rankings-cols" id="rankings-cols">
      <div class="rankings-header" id="rankings-header"></div>
      <div class="rankings-body" id="rankings-body"></div>
    </div>
  </div>
</div>

<script>
{script_block}
</script>
<script>
{shared_js}
</script>

</body>
</html>
"""


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    shared_css = (ROOT / "shared.css").read_text()
    shared_js = (ROOT / "shared.js").read_text()

    teams = load("teams.json")
    team_names = {t["name"] for t in teams}
    teams_js = "const teams = [\n" + "\n".join(
        '  {"name": %s, "shorthand": %s, "confederation": %s, "flag": %s},'
        % (json.dumps(t["name"]), json.dumps(t["shorthand"]), json.dumps(t["confederation"]), json.dumps(t["flag"]))
        for t in teams
    ) + "\n];"

    for year in YEARS:
        data_path = ROOT / "data" / f"{year}.json"
        data = json.load(open(data_path))
        try:
            validate(data, year, team_names)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

        games = derive_elos(data)

        if isinstance(data, dict):
            data["games"] = games
            data_path.write_text(json.dumps(data, indent=2) + "\n")

        games_js = f"const games{year} = " + json.dumps(games, indent=2) + ";"

        team_elos_js = None
        if isinstance(data, dict) and "teamElos" in data:
            team_elos_js = f"const teamElos{year} = " + json.dumps(data["teamElos"], separators=(',', ':')) + ";"

        config = PER_YEAR_CONFIG[year]
        script_block = build_script_block(year, games_js, teams_js, team_elos_js, config)
        html = page_html(year, script_block, shared_css, shared_js)

        path = ROOT / "site" / "football" / "worldcup" / f"{year}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html)
        print(f"Updated site/football/worldcup/{year}.html")

    history_html = build_history_page(shared_css)
    history_path = ROOT / "site" / "football" / "worldcup" / "history.html"
    history_path.write_text(history_html)
    print("Updated site/football/worldcup/history.html")


if __name__ == "__main__":
    main()
