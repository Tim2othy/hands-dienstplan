"""Read the Hands-Dienstplan from Google Sheets and write dienstplan.ics.

Configure LINK and NAME in config.py (gitignored), then run:

    python main.py
"""

from pathlib import Path

import config
from dienstplan import extract_shifts, fetch_rows
from icswriter import write_ics

OUTPUT = Path(__file__).with_name("dienstplan.ics")


def main() -> None:
    print(f"Fetching sheet for {config.NAME} ...")
    rows = fetch_rows(config.LINK)

    shifts = extract_shifts(rows, config.NAME)
    if not shifts:
        print("No shifts found - is the name and the sheet tab (gid) correct?")
        return

    for shift in shifts:
        print(
            f"  {shift.start:%d.%m.%Y %H:%M}-{shift.end:%H:%M}  "
            f"{shift.ort} | {shift.taetigkeit} | {shift.produktionsleitung}"
        )

    write_ics(shifts, config.NAME, OUTPUT)
    print(f"\n{len(shifts)} events written to {OUTPUT}")
    print(
        "Import it at https://calendar.google.com/calendar/r/settings/export "
        '("Import & export" -> "Import").'
    )


if __name__ == "__main__":
    main()
