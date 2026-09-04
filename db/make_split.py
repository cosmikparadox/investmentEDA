"""Generate the holdout split: which ISO weeks the dashboard is not allowed to show.

Run once, ever. It writes db/split_mask.csv, which is committed to git so the
split can never drift. If the file already exists this script checks that it
still matches and refuses to overwrite it unless you pass --force.

Why a holdout at all: a pattern you found by staring at a chart can only be
tested honestly on data you have never stared at. So a quarter of all weeks are
hidden from every exploration view, kept in reserve for testing a logged
observation later.

Why whole ISO weeks and not random days: adjacent days in a time series are not
independent. Monday tells you most of what Tuesday will say. Holding out single
days leaks the answer into the days either side of them; holding out whole
blocks does not.

Run with:  uv run python db/make_split.py
"""

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

# --- The three numbers that define the split. Never change these. ------------
SEED = 20260904        # fixed seed, so the same weeks are chosen every time
HOLDOUT_FRACTION = 0.25
FIRST_YEAR = 2015
LAST_YEAR = 2030

OUT_PATH = Path(__file__).parent / "split_mask.csv"


def iso_weeks(first_year: int, last_year: int) -> list[str]:
    """Every ISO week label from first_year to last_year, e.g. '2015-W01'.

    An ISO week always starts on a Monday, and a year has 52 or 53 of them.
    Rather than work that out, we walk one Monday at a time and ask Python
    which ISO year and week each Monday belongs to.
    """
    # Start on the Monday of the first ISO week of first_year. 4 January is
    # always in ISO week 1, by definition, so step back to its Monday.
    jan4 = date(first_year, 1, 4)
    day = jan4 - timedelta(days=jan4.isoweekday() - 1)

    weeks: list[str] = []
    while True:
        iso_year, iso_week, _ = day.isocalendar()
        if iso_year > last_year:
            break
        weeks.append(f"{iso_year}-W{iso_week:02d}")
        day += timedelta(days=7)
    return weeks


def build_rows() -> list[tuple[str, str]]:
    """Return (iso_week, split) pairs, sorted by week, with 25% marked holdout."""
    weeks = iso_weeks(FIRST_YEAR, LAST_YEAR)

    # random.Random(SEED) is a private random number generator seeded with a
    # fixed number, so it makes the same "random" choices on every machine.
    rng = random.Random(SEED)
    n_holdout = round(len(weeks) * HOLDOUT_FRACTION)
    holdout = set(rng.sample(weeks, n_holdout))

    return [(w, "holdout" if w in holdout else "explore") for w in weeks]


def write_csv(rows: list[tuple[str, str]], path: Path) -> None:
    with path.open("w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["iso_week", "split"])
        writer.writerows(rows)


def read_csv(path: Path) -> list[tuple[str, str]]:
    with path.open(newline="") as fh:
        reader = csv.reader(fh)
        next(reader)  # skip the header row
        return [(r[0], r[1]) for r in reader]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing split_mask.csv (you almost certainly should not)",
    )
    args = parser.parse_args()

    rows = build_rows()
    n_holdout = sum(1 for _, split in rows if split == "holdout")

    if OUT_PATH.exists() and not args.force:
        existing = read_csv(OUT_PATH)
        if existing == rows:
            print(f"{OUT_PATH} already exists and matches. Nothing to do.")
            return
        raise SystemExit(
            f"{OUT_PATH} already exists and DIFFERS from what this script now "
            f"produces. The split is committed to git and must never change. "
            f"Investigate before doing anything; --force only if you are certain."
        )

    write_csv(rows, OUT_PATH)
    print(
        f"Wrote {OUT_PATH} — {len(rows)} ISO weeks "
        f"({FIRST_YEAR}-W01 to {rows[-1][0]}), {n_holdout} marked holdout "
        f"({n_holdout / len(rows):.1%}). Commit this file. It never changes again."
    )


if __name__ == "__main__":
    main()
