#!/usr/bin/env python3
"""Set the result of a game and regenerate the HTML pages.

Usage:
  scripts/set_result.py YEAR GAME_NUMBER HOME_SCORE AWAY_SCORE [ELO_CHANGE --gains {home|away}]
  scripts/set_result.py --list-teams

Example:
  scripts/set_result.py 2026 13 1 1 15 --gains away

GAME_NUMBER is the game's 1-based position in chronological order within
that World Cup (shown as the "#" column on the page).

ELO_CHANGE is a positive integer (the magnitude of the transfer).
--gains specifies which team gains that ELO (home or away); required when
ELO_CHANGE is provided.

Sets the game's homeScore/awayScore (and eloChange if provided) in
data/YEAR.json, then runs build.py to derive homeEloPre/awayEloPre for
all games and regenerate the embedded data in all three *.html pages.

--list-teams prints the index of every team's shorthand, full name, and
confederation, from data/teams.json.
"""
import argparse
import json
import sys
from pathlib import Path

import build

ROOT = Path(__file__).resolve().parent.parent


def load_teams():
    return json.load(open(ROOT / "data" / "teams.json"))


def list_teams():
    teams = load_teams()
    width = max(len(t["name"]) for t in teams)
    for t in sorted(teams, key=lambda t: t["name"]):
        print(f"{t['shorthand']}  {t['name']:<{width}}  {t['confederation']}")


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)

    if len(sys.argv) == 2 and sys.argv[1] == "--list-teams":
        list_teams()
        sys.exit(0)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("year")
    parser.add_argument("game_number", type=int)
    parser.add_argument("home_score", type=int)
    parser.add_argument("away_score", type=int)
    parser.add_argument("elo_change", type=int, nargs="?", default=None)
    parser.add_argument("--gains", choices=["home", "away"], default=None)
    args = parser.parse_args()

    if (args.elo_change is not None) != (args.gains is not None):
        sys.exit("ELO_CHANGE and --gains must be supplied together.")
    if args.elo_change is not None and args.elo_change < 0:
        sys.exit("ELO_CHANGE must be a positive number.")

    path = ROOT / "data" / f"{args.year}.json"
    data = json.load(open(path))
    games = data["games"] if isinstance(data, dict) else data

    matches = [g for g in games if g["gameNumber"] == args.game_number]
    if not matches:
        sys.exit(f"No game number {args.game_number} found in {args.year}")

    game = matches[0]
    game["homeScore"] = args.home_score
    game["awayScore"] = args.away_score
    if args.elo_change is not None:
        sign = 1 if args.gains == "home" else -1
        game["eloChange"] = sign * args.elo_change

    if isinstance(data, dict):
        data["games"] = games
        path.write_text(json.dumps(data, indent=2) + "\n")
    else:
        path.write_text(json.dumps(games, indent=2) + "\n")

    print(f"Updated {path}: #{args.game_number} {game['homeTeam']} {args.home_score}-{args.away_score} {game['awayTeam']}"
          + (f", eloChange={game['eloChange']}" if args.elo_change is not None else ""))

    build.main()


if __name__ == "__main__":
    main()
