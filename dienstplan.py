"""Parse a Hands-Dienstplan Google Sheet into calendar events.

The sheet layout (as of 2026):

  * Row 1 holds the dates.  Every day occupies a block of 5 columns,
    starting at column C: C-G is day 1, H-L day 2, and so on.
  * Rows 2-4 are headers.
  * From row 5 downwards each person owns 3 consecutive rows (one per
    possible shift on the same day).  The name is in column A of the
    first of those rows.
  * The 5 columns of a day block are:
        Ort | Taetigkeit | Produktionsleitung | Dienstbeginn | Dauer in h
"""

from __future__ import annotations

import csv
import io
import re
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta

DATE_ROW = 0          # row 1, zero-based
FIRST_DAY_COL = 2     # column C, zero-based
BLOCK_WIDTH = 5       # columns per day
ROWS_PER_PERSON = 3   # a person can have up to 3 shifts per day
NAME_COL = 0  # column A

# The sheet has the year typed as 2027 by mistake; day and month are correct.
# Set to None to use whatever year the sheet says.
FORCE_YEAR: int | None = 2026

DATE_RE = re.compile(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})")
# "16:00 - 19:00 Uhr", "16:15-18:15", "16.00 – 19.00", "ab 16:00"
TIME_RE = re.compile(r"(\d{1,2})[:.](\d{2})")
DURATION_RE = re.compile(r"(\d+(?:[.,]\d+)?)")


@dataclass
class Shift:
    day: date
    ort: str
    taetigkeit: str
    produktionsleitung: str
    start: datetime
    end: datetime

    @property
    def summary(self) -> str:
        return f"Hands: {self.ort}" if self.ort else "Hands"

    @property
    def description(self) -> str:
        lines = []
        if self.taetigkeit:
            lines.append(f"TÄ: {self.taetigkeit}")
        if self.produktionsleitung:
            lines.append(f"PL: {self.produktionsleitung}")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# fetching
# --------------------------------------------------------------------------

def csv_export_url(link: str) -> str:
    """Turn a normal Google Sheets link into its CSV export URL."""
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", link)
    if not match:
        raise ValueError(f"Could not find a spreadsheet id in: {link!r}")
    sheet_id = match.group(1)

    gid_match = re.search(r"[#&?]gid=(\d+)", link)
    gid = gid_match.group(1) if gid_match else "0"

    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        f"/export?format=csv&gid={gid}"
    )


def fetch_rows(link: str) -> list[list[str]]:
    """Download the sheet and return it as a list of rows of strings."""
    url = csv_export_url(link)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request) as response:
        if "text/csv" not in response.headers.get("Content-Type", ""):
            raise RuntimeError(
                "Google did not return CSV. Make sure the sheet is shared with "
                "'anyone with the link' (viewer is enough)."
            )
        raw = response.read().decode("utf-8-sig")
    return list(csv.reader(io.StringIO(raw)))


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def cell(rows: list[list[str]], row: int, col: int) -> str:
    """Cell content, tolerating ragged/short rows."""
    if 0 <= row < len(rows) and 0 <= col < len(rows[row]):
        return rows[row][col].replace("\xa0", " ").strip()
    return ""


def parse_date(text: str) -> date | None:
    match = DATE_RE.search(text)
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    if year < 100:
        year += 2000
    if FORCE_YEAR is not None:
        year = FORCE_YEAR
    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_times(day: date, dienstbeginn: str, dauer: str) -> tuple[datetime, datetime] | None:
    """Return (start, end) for a shift, or None if there is no usable time."""
    times = TIME_RE.findall(dienstbeginn)
    if not times:
        return None

    hour, minute = (int(part) for part in times[0])
    start = datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute)

    if len(times) >= 2:
        hour, minute = (int(part) for part in times[1])
        end = datetime.combine(day, datetime.min.time()).replace(hour=hour, minute=minute)
        if end <= start:  # shift running past midnight
            end += timedelta(days=1)
        return start, end

    # only a start time: fall back to the "Dauer in h" column
    duration_match = DURATION_RE.search(dauer)
    hours = float(duration_match.group(1).replace(",", ".")) if duration_match else 1.0
    return start, start + timedelta(hours=hours)


def find_name_row(rows: list[list[str]], name: str) -> int:
    """Zero-based index of the row whose column A holds `name`."""
    wanted = name.strip().casefold()
    for index, _ in enumerate(rows):
        value = cell(rows, index, NAME_COL).casefold()
        if value and (value == wanted or wanted in value):
            return index
    raise LookupError(
        f"Could not find {name!r} in column A of the sheet. " "Check NAME in config.py."
    )


# --------------------------------------------------------------------------
# parsing
# --------------------------------------------------------------------------

def extract_shifts(rows: list[list[str]], name: str) -> list[Shift]:
    first_row = find_name_row(rows, name)
    person_rows = range(first_row, first_row + ROWS_PER_PERSON)

    shifts: list[Shift] = []
    col = FIRST_DAY_COL
    while col < max((len(row) for row in rows), default=0):
        day = parse_date(cell(rows, DATE_ROW, col))
        if day is not None:
            for row in person_rows:
                ort = cell(rows, row, col)
                taetigkeit = cell(rows, row, col + 1)
                produktionsleitung = cell(rows, row, col + 2)
                dienstbeginn = cell(rows, row, col + 3)
                dauer = cell(rows, row, col + 4)

                if not any((ort, taetigkeit, dienstbeginn)):
                    continue  # empty shift slot

                times = parse_times(day, dienstbeginn, dauer)
                if times is None:
                    print(
                        f"  ! {day:%d.%m.%Y} {ort or taetigkeit!r}: no readable "
                        f"time in {dienstbeginn!r} - skipped"
                    )
                    continue

                start, end = times
                shifts.append(
                    Shift(day, ort, taetigkeit, produktionsleitung, start, end)
                )
        col += BLOCK_WIDTH

    shifts.sort(key=lambda shift: shift.start)
    return shifts
