"""Load recipient organizations and their published intake constraints."""

from __future__ import annotations

import json
from pathlib import Path

from strands import tool

from ..models import OpenWindow, Recipient

DEFAULT_PATH = Path(__file__).resolve().parents[3] / "data" / "recipients.json"


def load_recipients(path: str | Path = DEFAULT_PATH) -> list[Recipient]:
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    out: list[Recipient] = []
    for r in raw["recipients"]:
        windows = r.get("open_windows")
        out.append(
            Recipient(
                recipient_id=r["recipient_id"],
                name=r["name"],
                org_type=r["org_type"],
                address=r["address"],
                service_area=r["service_area"],
                contact_email=r.get("contact_email"),
                contact_phone=r.get("contact_phone"),
                open_windows=(
                    [OpenWindow(**w) for w in windows] if windows else None
                ),
                accepts=r["accepts"],
                min_pickup_lbs=r.get("min_pickup_lbs"),
                offers_pickup=r["offers_pickup"],
                pickup_lead_time_minutes=r.get("pickup_lead_time_minutes"),
                has_refrigerated_transport=r.get("has_refrigerated_transport"),
                constraints_notes=r["constraints_notes"],
                source_url=r["source_url"],
            )
        )
    return out


@tool
def list_recipients() -> str:
    """List every food recovery organization and what it publicly accepts.

    Call this first: the eligibility and scheduling tools take a
    recipient_id, and this is where those identifiers come from.

    Returns:
        JSON roster with each organization's id, name, service area, accepted
        food categories, pickup minimum, published hours and source URL.
        A null field means the organization does not publish that constraint,
        which has to be confirmed with them rather than assumed.
    """
    roster = [
        {
            "recipient_id": r.recipient_id,
            "name": r.name,
            "org_type": r.org_type,
            "service_area": r.service_area,
            "accepts": r.accepts,
            "min_pickup_lbs": r.min_pickup_lbs,
            "offers_pickup": r.offers_pickup,
            "open_windows": (
                [{"days": w.days, "start": w.start, "end": w.end, "note": w.note}
                 for w in r.open_windows] if r.open_windows else None
            ),
            "contact_email": r.contact_email,
            "constraints_notes": r.constraints_notes,
            "source": r.source_url,
        }
        for r in load_recipients()
    ]
    return json.dumps(roster, indent=2)
