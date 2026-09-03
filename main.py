"""Read the Hands-Dienstplan from Google Sheets and write dienstplan.ics.

Configure LINK and NAME in config.py (gitignored), then run:

    python main.py
"""

from pathlib import Path

import config
from checks import check
from dienstplan import extract_shifts, fetch_rows
from icswriter import write_ics

OUTPUT = Path(__file__).with_name("dienstplan.ics")


def main() -> None:
    print(f"Fetching sheet for {config.NAME} ...")
    rows = fetch_rows(config.LINK)

    result = extract_shifts(rows, config.NAME)
    write_ics(result.shifts, config.NAME, OUTPUT)
    print(f"{len(result.shifts)} events written to {OUTPUT}")

    problems = check(result, OUTPUT)
    if problems:
        print()
        print("!" * 72)
        print("!!!  WARNING: something is broken - the .ics is INCOMPLETE  !!!")
        print("!" * 72)
        for problem in problems:
            print(f"  - {problem}")
        print("!" * 72)
        return

    print(
        "Import it at https://calendar.google.com/calendar/r/settings/export "
        '("Import & export" -> "Import").'
    )


if __name__ == "__main__":
    main()
