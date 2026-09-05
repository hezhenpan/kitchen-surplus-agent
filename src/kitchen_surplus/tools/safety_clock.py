"""Deterministic TCS clock arithmetic.

The Safety Agent decides *whether* an item is TCS (a judgement call about a
free-text menu name). This module decides *how long it stays safe*, which is
pure arithmetic against rules/tcs_rules.yaml and must never be improvised by a
model.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

import yaml
from strands import tool

RULES_PATH = Path(__file__).resolve().parents[3] / "rules" / "tcs_rules.yaml"


@lru_cache(maxsize=1)
def load_rules() -> dict:
    with open(RULES_PATH, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@tool
def compute_hold_window(
    item_name: str,
    is_tcs: bool,
    holding_state: str,
    prepared_at: str,
    last_temp_f: float | None = None,
    last_temp_check_at: str | None = None,
    evaluated_at: str | None = None,
) -> str:
    """Compute how much longer an item stays safe under TCS rules.

    Args:
        item_name: Menu name of the item.
        is_tcs: Whether the item requires time/temperature control, as
            classified by the Safety Agent.
        holding_state: One of "hot", "cold", "ambient".
        prepared_at: ISO timestamp when the item was prepared.
        last_temp_f: Most recent measured temperature in Fahrenheit, if any.
        last_temp_check_at: ISO timestamp of that measurement, if any.
        evaluated_at: ISO timestamp to evaluate against; defaults to now.

    Returns:
        JSON with `donatable`, `safe_until`, `minutes_remaining`, the rule that
        governed the decision, and its citation.
    """
    rules = load_rules()["thresholds"]
    now = datetime.fromisoformat(evaluated_at) if evaluated_at else datetime.now()
    prepared = datetime.fromisoformat(prepared_at)
    checked = datetime.fromisoformat(last_temp_check_at) if last_temp_check_at else None

    def result(donatable: bool, safe_until: datetime | None, rule_key: str,
               reason: str) -> str:
        rule = rules.get(rule_key, {})
        remaining = (
            int((safe_until - now).total_seconds() // 60) if safe_until else None
        )
        return json.dumps({
            "item_name": item_name,
            "donatable": donatable and (remaining is None or remaining > 0),
            "safe_until": safe_until.isoformat() if safe_until else None,
            "minutes_remaining": remaining,
            "reason": reason,
            "rule": rule.get("rule"),
            "source": rule.get("source"),
        }, indent=2)

    if not is_tcs:
        return result(True, None, "", "Not a TCS food; no time/temperature clock applies.")

    danger_low = rules["danger_zone_f"]["low"]
    danger_high = rules["danger_zone_f"]["high"]
    danger_hours = rules["danger_zone_max_hours"]["value"]

    # Measured temperature always wins over the nominal holding state: a "hot"
    # line item reading 129F is in the danger zone regardless of intent.
    if last_temp_f is not None and danger_low <= last_temp_f <= danger_high:
        # Conservative: the clock starts at the measurement we can evidence.
        # Without a measurement we would have to assume preparation time.
        start = checked or prepared
        return result(
            True, start + timedelta(hours=danger_hours), "danger_zone_max_hours",
            f"Measured {last_temp_f}F is inside the {danger_low}-{danger_high}F "
            f"danger zone; {danger_hours}h clock started {start.isoformat()}.",
        )

    if holding_state == "hot":
        min_hot = rules["hot_holding_min_f"]["value"]
        if last_temp_f is not None and last_temp_f < min_hot:
            return result(False, None, "hot_holding_min_f",
                          f"Measured {last_temp_f}F is below the {min_hot}F "
                          "hot-holding minimum for received product.")
        window = rules["hot_food_service_window_hours"]["value"]
        return result(True, now + timedelta(hours=window),
                      "hot_food_service_window_hours",
                      f"Held at {last_temp_f}F; must be served within "
                      f"{window}h of donation.")

    if holding_state == "cold":
        max_cold = rules["cold_holding_max_f"]["value"]
        if last_temp_f is not None and last_temp_f > max_cold:
            return result(False, None, "cold_holding_max_f",
                          f"Measured {last_temp_f}F exceeds the {max_cold}F "
                          "cold-holding limit.")
        return result(True, None, "cold_holding_max_f",
                      f"Held at {last_temp_f}F; safe while the cold chain is "
                      "maintained through pickup.")

    # Ambient TCS food with no usable measurement: clock from preparation.
    return result(True, prepared + timedelta(hours=danger_hours),
                  "danger_zone_max_hours",
                  "Ambient TCS food with no temperature evidence; clock "
                  f"conservatively started at preparation ({prepared.isoformat()}).")
