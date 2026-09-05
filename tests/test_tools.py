"""The deterministic layer must hold without a model in the loop."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kitchen_surplus.tools import (  # noqa: E402
    build_chill_plan, check_intake_eligibility, compute_hold_window,
    load_recipients, load_surplus_items, next_open_window,
)

CLOSE = "2026-09-05T21:30"
EXPORT = Path(__file__).resolve().parents[1] / "data" / "pos_eod_sample.csv"


def call(tool, **kwargs):
    return json.loads(getattr(tool, "func", tool)(**kwargs))


def test_export_parses_only_leftovers():
    items = load_surplus_items(EXPORT)
    assert items
    assert all(item.remaining_qty > 0 for item in items)


def test_non_tcs_food_has_no_clock():
    r = call(compute_hold_window, item_name="Dinner Rolls", is_tcs=False,
             holding_state="ambient", prepared_at="2026-09-05T13:30",
             evaluated_at=CLOSE)
    assert r["donatable"] is True
    assert r["safe_until"] is None


def test_measured_temperature_overrides_holding_state():
    """A 'hot' line item reading 129F is in the danger zone regardless."""
    r = call(compute_hold_window, item_name="Kung Pao Chicken", is_tcs=True,
             holding_state="hot", prepared_at="2026-09-05T15:30",
             last_temp_f=129.0, last_temp_check_at="2026-09-05T21:00",
             evaluated_at=CLOSE)
    assert "danger zone" in r["reason"]
    assert r["source"] == "FDA Food Code 3-501.19"


def test_expired_danger_zone_item_is_refused():
    r = call(compute_hold_window, item_name="Yangzhou Fried Rice", is_tcs=True,
             holding_state="ambient", prepared_at="2026-09-05T14:30",
             last_temp_f=88.0, last_temp_check_at="2026-09-05T16:30",
             evaluated_at=CLOSE)
    assert r["donatable"] is False
    assert r["minutes_remaining"] < 0


def test_chill_plan_uses_two_stage_cooling():
    r = call(build_chill_plan, item_name="Rotisserie Chicken",
             current_temp_f=141.0, start_at=CLOSE)
    assert r["applicable"] is True
    stage_1, stage_2 = r["checkpoints"]
    assert stage_1["target_f"] == 70 and stage_1["by"] == "2026-09-05T23:30:00"
    assert stage_2["target_f"] == 41 and stage_2["by"] == "2026-09-06T03:30:00"
    assert all(c["source"] == "FDA Food Code 3-501.14" for c in r["checkpoints"])


def test_food_bank_that_refuses_restaurant_food_is_ineligible():
    r = call(check_intake_eligibility, recipient_id="REC-SFMFB-SF",
             food_class="cold_prepared", weight_lbs=30.0)
    assert r["eligible"] is False


def test_pickup_minimum_blocks_a_small_donation():
    r = call(check_intake_eligibility, recipient_id="REC-WPE-CONCORD",
             food_class="cold_prepared", weight_lbs=111.7)
    assert r["eligible"] is False
    assert "300 lb pickup minimum" in r["blockers"][0]


def test_unpublished_hours_are_not_treated_as_open():
    r = call(next_open_window, recipient_id="REC-FOODRUNNERS-SF", after=CLOSE)
    assert r["windows_published"] is False
    assert "opens_at" not in r


def test_saturday_close_leaves_food_banks_shut_until_monday():
    """The gap that makes rapid chilling the decisive action."""
    r = call(next_open_window, recipient_id="REC-ACCFB-OAKLAND", after=CLOSE)
    assert r["opens_at"].startswith("2026-09-07")
    assert r["hours_until"] > 24


def test_every_recipient_constraint_is_sourced():
    for recipient in load_recipients():
        assert recipient.source_url.startswith("https://")
