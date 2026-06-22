#!/usr/bin/env python3
"""Regenerate the embedded data blocks in 2018.html / 2022.html / 2026.html
from data/*.json. Run this after editing any data/*.json file by hand,
or use scripts/set_result.py for a one-line score update.

For tournament files that include a top-level "teamElos" key, homeEloPre and
awayEloPre are derived automatically and written back to the JSON before the
HTML is regenerated.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YEARS = [2018, 2022, 2026]


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


def replace_block(html, name, content):
    """Replace the content between // BEGIN:name and // END:name sentinels."""
    pattern = rf'// BEGIN:{re.escape(name)}\n.*?// END:{re.escape(name)}'
    replacement = f'// BEGIN:{name}\n{content}\n// END:{name}'
    result, n = re.subn(pattern, replacement, html, flags=re.DOTALL)
    if n == 0:
        raise ValueError(f"Sentinel '// BEGIN:{name}' not found in {html[:40]!r}...")
    return result


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


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

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

        path = ROOT / f"{year}.html"
        html = path.read_text()
        html = replace_block(html, f"games{year}", games_js)
        html = replace_block(html, "teams", teams_js)
        if isinstance(data, dict) and "teamElos" in data:
            team_elos_js = f"const teamElos{year} = " + json.dumps(data["teamElos"], separators=(',', ':')) + ";"
            html = replace_block(html, f"teamElos{year}", team_elos_js)
        path.write_text(html)
        print(f"Updated {year}.html")


if __name__ == "__main__":
    main()
