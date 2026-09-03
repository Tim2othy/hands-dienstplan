"""Sanity checks: did every shift in the sheet make it into the .ics file?

Every entry in the sheet fills all five of its columns (Ort, Taetigkeit,
Produktionsleitung, Dienstbeginn, Dauer in h).  So those five counts must
agree with each other, and with the number of events in the written file.
If they do not, the parser lost something.
"""

from __future__ import annotations

from pathlib import Path

from dienstplan import ParseResult


def count_events(ics_path: Path) -> int:
    """Number of VEVENTs in a written .ics file."""
    text = ics_path.read_text(encoding="utf-8")
    return sum(1 for line in text.splitlines() if line.strip() == "BEGIN:VEVENT")


def check(result: ParseResult, ics_path: Path) -> list[str]:
    """Return a list of problems; empty means everything lines up."""
    problems = list(result.problems)

    events = count_events(ics_path)
    counts = result.filled

    if len(set(counts.values())) > 1:
        detail = ", ".join(f"{column}: {count}" for column, count in counts.items())
        problems.append(f"the 5 columns are not filled equally often ({detail})")

    for column, count in counts.items():
        if count != events:
            problems.append(
                f"column {column!r} is filled {count} times, "
                f"but the .ics has {events} events"
            )

    if events != len(result.shifts):
        problems.append(
            f"{len(result.shifts)} shifts were parsed but the .ics has {events} events"
        )

    return problems
