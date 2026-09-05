"""Check an item against a recipient's published intake constraints."""

from __future__ import annotations

import json

from strands import tool

from .recipients import load_recipients

FOOD_CLASSES = ("hot_prepared", "cold_prepared", "produce",
                "dairy_meat", "shelf_stable")


@tool
def check_intake_eligibility(
    recipient_id: str,
    food_class: str,
    weight_lbs: float,
    needs_pickup: bool = True,
) -> str:
    """Test one item against what a recipient publicly says it accepts.

    Args:
        recipient_id: Recipient identifier from data/recipients.json.
        food_class: One of hot_prepared, cold_prepared, produce, dairy_meat,
            shelf_stable -- assigned by the agent from the menu item.
        weight_lbs: Weight of the proposed donation.
        needs_pickup: Whether the donor needs the recipient to collect.

    Returns:
        JSON with `eligible`, the blocking reasons, and the source URL for
        each constraint applied.
    """
    if food_class not in FOOD_CLASSES:
        return json.dumps({
            "error": f"unknown food_class {food_class!r}",
            "expected": list(FOOD_CLASSES),
        })
    recipient = next(
        (r for r in load_recipients() if r.recipient_id == recipient_id), None
    )
    if recipient is None:
        return json.dumps({"error": f"unknown recipient_id {recipient_id}"})

    blockers: list[str] = []
    if not recipient.accepts.get(food_class, False):
        blockers.append(
            f"{recipient.name} does not list {food_class} among accepted "
            f"categories."
        )
    if needs_pickup and not recipient.offers_pickup:
        blockers.append(f"{recipient.name} does not offer pickup.")
    if (needs_pickup and recipient.min_pickup_lbs
            and weight_lbs < recipient.min_pickup_lbs):
        blockers.append(
            f"{weight_lbs:.1f} lb is below the published "
            f"{recipient.min_pickup_lbs:.0f} lb pickup minimum."
        )

    return json.dumps({
        "recipient_id": recipient_id,
        "recipient_name": recipient.name,
        "eligible": not blockers,
        "blockers": blockers,
        "constraints_notes": recipient.constraints_notes,
        "source": recipient.source_url,
    }, indent=2)
