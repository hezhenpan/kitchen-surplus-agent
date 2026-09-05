"""Two-stage cooling plan for hot TCS food (FDA Food Code 3-501.14).

Rapid chilling is the action that decides whether tonight's hot surplus still
exists tomorrow morning. It is not advice -- it is a timed procedure with
checkpoints, and those checkpoints are themselves the temperature record the
generator has to keep.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta

from strands import tool

from .safety_clock import load_rules


@tool
def build_chill_plan(
    item_name: str,
    current_temp_f: float,
    start_at: str,
    danger_zone_entered_at: str | None = None,
) -> str:
    """Produce the cooling checkpoints that keep a hot item donatable.

    Args:
        item_name: Menu name of the item.
        current_temp_f: Current temperature in Fahrenheit.
        start_at: ISO timestamp when cooling begins.
        danger_zone_entered_at: ISO timestamp the item first entered the
            42-134F danger zone, if it already had. Time already spent there
            is deducted from the cooling schedule -- the two-stage schedule
            assumes food leaving the stove above 135F, and an item that has
            been sitting at 96F does not get the full six hours.

    Returns:
        JSON with the two cooling checkpoints, the resulting cold-holding
        state, and the action required if a checkpoint is missed.
    """
    rules = load_rules()["thresholds"]
    s1, s2 = rules["cooling_stage_one"], rules["cooling_stage_two"]
    fail = rules["cooling_failure_action"]
    start = datetime.fromisoformat(start_at)

    if current_temp_f <= s2["to_f"]:
        return json.dumps({
            "item_name": item_name,
            "applicable": False,
            "reason": f"Already at or below {s2['to_f']}F; no cooling needed.",
        })

    check_1 = start + timedelta(hours=s1["max_hours"])
    check_2 = start + timedelta(hours=s2["total_max_hours"])

    # An item already in the danger zone has a running 4-hour clock. Cooling
    # does not reset it, so the schedule may not run past it.
    danger_deadline: datetime | None = None
    capped = False
    if danger_zone_entered_at is not None:
        entered = datetime.fromisoformat(danger_zone_entered_at)
        danger_deadline = entered + timedelta(
            hours=rules["danger_zone_max_hours"]["value"]
        )
        if danger_deadline <= start:
            return json.dumps({
                "item_name": item_name,
                "applicable": False,
                "reason": (
                    f"The 4-hour danger-zone clock ran out at "
                    f"{danger_deadline.isoformat()}, before cooling would "
                    f"start. Cooling cannot restart an expired clock."
                ),
                "source": rules["danger_zone_max_hours"]["source"],
            }, indent=2)
        if danger_deadline < check_2:
            check_2 = danger_deadline
            capped = True
        if danger_deadline < check_1:
            check_1 = danger_deadline

    return json.dumps({
        "danger_zone_deadline": (
            danger_deadline.isoformat() if danger_deadline else None
        ),
        "schedule_capped_by_danger_zone": capped,
        "item_name": item_name,
        "applicable": True,
        "start_at": start.isoformat(),
        "checkpoints": [
            {
                "by": check_1.isoformat(),
                "target_f": s1["to_f"],
                "rule": s1["rule"],
                "source": s1["source"],
                "on_miss": fail["rule"],
            },
            {
                "by": check_2.isoformat(),
                "target_f": s2["to_f"],
                "rule": s2["rule"],
                "source": s2["source"],
                "on_miss": fail["rule"],
            },
        ],
        "note": (
            "Cooling schedule shortened: this item was already in the danger "
            "zone, and that clock keeps running while it cools."
            if capped else None
        ),
        "result_if_met": {
            "holding_state": "cold",
            "note": (
                f"Once at or below {s2['to_f']}F the 4-hour danger-zone clock "
                "no longer applies; the item stays donatable while the cold "
                "chain is maintained through pickup."
            ),
        },
    }, indent=2)
