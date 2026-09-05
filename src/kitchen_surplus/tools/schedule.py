"""Recipient availability arithmetic.

Whether a recipient is open is a published fact plus calendar maths, so it
belongs in a tool. Whether an unpublished window means "closed" or "ask them"
is a judgement, and stays with the Matching Agent.
"""

from __future__ import annotations

import json
from datetime import datetime, time, timedelta

from strands import tool

from .recipients import load_recipients

_DAY_INDEX = {"mon": 0, "tue": 1, "wed": 2, "thu": 3,
              "fri": 4, "sat": 5, "sun": 6}


def _expand_days(spec: str) -> set[int]:
    """Expand a published day spec such as "Mon-Fri" or "Sun-Sat"."""
    spec = spec.strip().lower()
    if "-" not in spec:
        return {_DAY_INDEX[spec[:3]]}
    start, end = (part.strip()[:3] for part in spec.split("-", 1))
    a, b = _DAY_INDEX[start], _DAY_INDEX[end]
    if a <= b:
        return set(range(a, b + 1))
    return set(range(a, 7)) | set(range(0, b + 1))  # wraps the week


@tool
def next_open_window(recipient_id: str, after: str, horizon_days: int = 7) -> str:
    """Find the next time a recipient is open to receive food.

    Args:
        recipient_id: Recipient identifier from data/recipients.json.
        after: ISO timestamp to search forward from.
        horizon_days: How many days ahead to search.

    Returns:
        JSON with `opens_at`, `closes_at` and `hours_until`, or
        `windows_published: false` when the organization does not publish
        intake hours -- which means the answer must be obtained by asking them,
        not assumed.
    """
    recipient = next(
        (r for r in load_recipients() if r.recipient_id == recipient_id), None
    )
    if recipient is None:
        return json.dumps({"error": f"unknown recipient_id {recipient_id}"})

    start = datetime.fromisoformat(after)
    if not recipient.open_windows:
        return json.dumps({
            "recipient_id": recipient_id,
            "windows_published": False,
            "note": recipient.constraints_notes,
            "source": recipient.source_url,
        })

    best: tuple[datetime, datetime, str | None] | None = None
    for offset in range(horizon_days + 1):
        day = (start + timedelta(days=offset)).date()
        for window in recipient.open_windows:
            if day.weekday() not in _expand_days(window.days):
                continue
            opens = datetime.combine(day, time.fromisoformat(window.start))
            closes = datetime.combine(day, time.fromisoformat(window.end))
            if closes <= start:
                continue
            candidate = (max(opens, start), closes, window.note)
            if best is None or candidate[0] < best[0]:
                best = candidate
        if best is not None:
            break

    if best is None:
        return json.dumps({
            "recipient_id": recipient_id,
            "windows_published": True,
            "opens_at": None,
            "note": f"No open window within {horizon_days} days.",
        })

    opens_at, closes_at, note = best
    return json.dumps({
        "recipient_id": recipient_id,
        "windows_published": True,
        "opens_at": opens_at.isoformat(),
        "closes_at": closes_at.isoformat(),
        "hours_until": round((opens_at - start).total_seconds() / 3600, 1),
        "note": note,
        "source": recipient.source_url,
    })
