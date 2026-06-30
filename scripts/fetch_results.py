#!/usr/bin/env python3
"""Fetch yesterday's World Cup results from eloratings.net and update 2026.json.

Usage:
  scripts/fetch_results.py [--dry-run] [--all]

Fetches https://www.eloratings.net/latest.tsv, finds any WC games that are
in 2026.json with null scores but now have results, sets homeScore/awayScore
and eloChange, then runs build.py.

Options:
  --dry-run   Show what would change without writing anything.
  --all       Update all unscored games found in the TSV (default: only games
              played yesterday or earlier, to avoid partial-day updates).
"""
import argparse
import json
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

import build

ROOT = Path(__file__).resolve().parent.parent
YEAR = 2026
TSV_URL = "https://www.eloratings.net/latest.tsv"

# TSV 2-3 char codes → team names used in 2026.json / teams.json
CODE_MAP = {
    "AR": "Argentina",
    "AT": "Austria",
    "AU": "Australia",
    "BA": "Bosnia",
    "BE": "Belgium",
    "BR": "Brazil",
    "CA": "Canada",
    "CD": "DR Congo",
    "CH": "Switzerland",
    "CI": "Ivory Coast",
    "CO": "Colombia",
    "CV": "Cape Verde",
    "CW": "Curacao",
    "CZ": "Czechia",
    "DE": "Germany",
    "DZ": "Algeria",
    "EC": "Ecuador",
    "EG": "Egypt",
    "EN": "England",
    "ES": "Spain",
    "FR": "France",
    "GH": "Ghana",
    "HR": "Croatia",
    "HT": "Haiti",
    "IQ": "Iraq",
    "IR": "Iran",
    "JO": "Jordan",
    "JP": "Japan",
    "KR": "South Korea",
    "MA": "Morocco",
    "MX": "Mexico",
    "NL": "Netherlands",
    "NO": "Norway",
    "NZ": "New Zealand",
    "PA": "Panama",
    "PT": "Portugal",
    "PY": "Paraguay",
    "QA": "Qatar",
    "SA": "Saudi Arabia",
    "SE": "Sweden",
    "SN": "Senegal",
    "SQ": "Scotland",
    "TN": "Tunisia",
    "TR": "Turkey",
    "US": "USA",
    "UY": "Uruguay",
    "UZ": "Uzbekistan",
    "ZA": "South Africa",
}


def fetch_tsv():
    with urllib.request.urlopen(TSV_URL, timeout=10) as r:
        return r.read().decode()


def parse_wc_rows(tsv_text):
    """Return WC rows as dicts keyed by frozenset of the two team names.

    The TSV team ordering may differ from our home/away assignment (all games
    are played at neutral sites), so we store both orderings and flip signs as
    needed when matching against our game records.
    """
    results = {}
    for line in tsv_text.strip().split("\n"):
        cols = line.split("\t")
        if len(cols) < 10 or cols[7] != "WC":
            continue
        year, month, day = int(cols[0]), int(cols[1]), int(cols[2])
        code1, code2 = cols[3], cols[4]
        team1 = CODE_MAP.get(code1)
        team2 = CODE_MAP.get(code2)
        if team1 is None or team2 is None:
            print(f"  WARNING: unknown code(s): {code1!r} or {code2!r} — skipping row", file=sys.stderr)
            continue
        score1 = int(cols[5])
        score2 = int(cols[6])
        elo_change = int(cols[9])  # positive = team1 gained
        game_date = f"{year:04d}-{month:02d}-{day:02d}"
        # Store keyed by the TSV ordering so we can flip if needed
        results[frozenset([team1, team2])] = {
            "team1": team1,
            "team2": team2,
            "score1": score1,
            "score2": score2,
            "eloChange": elo_change,  # positive = team1 gained
            "date": game_date,
        }
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--all", action="store_true", help="Update all unscored games, not just past ones.")
    args = parser.parse_args()

    today = str(date.today())
    cutoff = today if args.all else str(date.today() - timedelta(days=0))  # include today too

    print(f"Fetching {TSV_URL} ...")
    try:
        tsv_text = fetch_tsv()
    except Exception as e:
        sys.exit(f"Failed to fetch TSV: {e}")

    tsv_results = parse_wc_rows(tsv_text)
    print(f"  {len(tsv_results)} WC results found in TSV.")

    path = ROOT / "data" / f"{YEAR}.json"
    data = json.load(open(path))
    games = data["games"]

    updates = []
    for game in games:
        if game.get("homeScore") is not None:
            continue  # already scored
        game_date = game.get("date", "")
        if not args.all and game_date and game_date > cutoff:
            continue  # future game
        key = frozenset([game["homeTeam"], game["awayTeam"]])
        if key not in tsv_results:
            continue
        tsv = tsv_results[key]
        # Determine scores from our home/away perspective (TSV may be flipped)
        if tsv["team1"] == game["homeTeam"]:
            home_score, away_score = tsv["score1"], tsv["score2"]
            elo_change = tsv["eloChange"]
        else:
            home_score, away_score = tsv["score2"], tsv["score1"]
            elo_change = -tsv["eloChange"]
        updates.append((game, home_score, away_score, elo_change))

    if not updates:
        print("Nothing to update — all played games are already scored.")
        return

    print(f"\n{'Would update' if args.dry_run else 'Updating'} {len(updates)} game(s):")
    for game, home_score, away_score, elo_change in updates:
        print(f"  #{game['gameNumber']:>2}  {game['homeTeam']} {home_score}-{away_score} {game['awayTeam']}, eloChange={elo_change:+d}")
        if not args.dry_run:
            game["homeScore"] = home_score
            game["awayScore"] = away_score
            game["eloChange"] = elo_change

    if args.dry_run:
        print("\n(dry run — no files written)")
        return

    data["games"] = games
    path.write_text(json.dumps(data, indent=2) + "\n")
    print("\nRebuilding HTML...")
    build.main()
    print("Done.")


if __name__ == "__main__":
    main()
