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
def build_chill_plan(item_name: str, current_temp_f: float, start_at: str) -> str:
    """Produce the cooling checkpoints that keep a hot item donatable.

    Args:
        item_name: Menu name of the item.
        current_temp_f: Current temperature in Fahrenheit.
        start_at: ISO timestamp when cooling begins.

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
    return json.dumps({
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
        "result_if_met": {
            "holding_state": "cold",
            "note": (
                f"Once at or below {s2['to_f']}F the 4-hour danger-zone clock "
                "no longer applies; the item stays donatable while the cold "
                "chain is maintained through pickup."
            ),
        },
    }, indent=2)
