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
YEARS = [2018, 2022, 2026]

# Per-year static configuration: gameset boundaries and the comment that
# describes the tournament format. These are the only parts of the page that
# differ by year beyond the data blocks.
PER_YEAR_CONFIG = {
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
    parts.append('<a href="../../index.html">Home</a>')
    return '<nav>' + ' | '.join(parts) + '</nav>'


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
<style>
{shared_css}
</style>
</head>
<body>
{nav}
<h1>World Cup ELO - {year}</h1>

<div class="page-toggle view-toggle">
  <button id="tab-matches" class="active" onclick="setPageView('matches')">Match List</button>
  <button id="tab-rankings" onclick="setPageView('rankings')">Rankings</button>
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


if __name__ == "__main__":
    main()
