"""Write shifts as an .ics file that Google Calendar can import."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

TIMEZONE = "Europe/Berlin"

# Google is happy with a TZID it already knows, but shipping the definition
# makes the file work in Outlook/Apple Calendar too.
VTIMEZONE = """BEGIN:VTIMEZONE
TZID:Europe/Berlin
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE"""


def escape(text: str) -> str:
    """Escape a value according to RFC 5545."""
    text = text.replace("\\", "\\\\")
    text = text.replace("\r\n", "\\n").replace("\n", "\\n")
    text = text.replace(";", "\\;").replace(",", "\\,")
    return text


def fold(line: str) -> str:
    """RFC 5545 asks for lines of at most 75 octets."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line

    chunks, current = [], b""
    for char in line:
        char_bytes = char.encode("utf-8")
        limit = 75 if not chunks else 74  # continuation lines start with a space
        if len(current) + len(char_bytes) > limit:
            chunks.append(current)
            current = b""
        current += char_bytes
    chunks.append(current)
    return "\r\n ".join(chunk.decode("utf-8") for chunk in chunks)


def local(moment: datetime) -> str:
    return moment.strftime("%Y%m%dT%H%M%S")


def uid(shift, name: str) -> str:
    """Stable id, so re-importing updates events instead of duplicating them."""
    seed = f"{name}|{shift.start.isoformat()}|{shift.ort}|{shift.taetigkeit}"
    return f"{hashlib.sha1(seed.encode('utf-8')).hexdigest()}@hands-dienstplan"


def build_calendar(shifts, name: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//hands-dienstplan//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        *VTIMEZONE.splitlines(),
    ]

    for shift in shifts:
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid(shift, name)}",
            f"DTSTAMP:{stamp}",
            f"DTSTART;TZID={TIMEZONE}:{local(shift.start)}",
            f"DTEND;TZID={TIMEZONE}:{local(shift.end)}",
            f"SUMMARY:{escape(shift.summary)}",
        ]
        if shift.ort:
            lines.append(f"LOCATION:{escape(shift.ort)}")
        if shift.description:
            lines.append(f"DESCRIPTION:{escape(shift.description)}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(line) for line in lines) + "\r\n"


def write_ics(shifts, name: str, path: Path) -> Path:
    path.write_text(build_calendar(shifts, name), encoding="utf-8", newline="")
    return path
