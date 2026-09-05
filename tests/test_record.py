"""Donation records must be complete or say why they are not."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kitchen_surplus.tools import (  # noqa: E402
    generate_donation_record, monthly_pounds_summary,
)

ITEMS = json.dumps([
    {"name": "Rotisserie Chicken", "weight_lbs": 30.0},
    {"name": "Clam Chowder", "weight_lbs": 6.0},
])
BASE = {
    "generator_name": "Demo Kitchen",
    "generator_address": "1 Market St, San Francisco, CA",
    "recipient_id": "REC-FOODRUNNERS-SF",
    "donated_at": "2026-09-06T09:15",
    "items_json": ITEMS,
}


def call(tool, **kwargs):
    return json.loads(getattr(tool, "func", tool)(**kwargs))


def test_record_carries_the_regulation_it_satisfies():
    r = call(generate_donation_record, **BASE)
    assert r["citation"] == "Cal. Code Regs. tit. 14, s 18991.4"
    assert r["pounds_donated"] == 36.0
    assert r["reporting_month"] == "2026-09"
    assert r["recipient"]["name"].startswith("Food Runners")


def test_missing_written_agreement_is_reported_not_hidden():
    """The commonest SB 1383 gap: no written agreement with the recipient."""
    r = call(generate_donation_record, **BASE)
    assert r["complete"] is False
    assert any("written agreement" in g for g in r["compliance_gaps"])


def test_missing_training_record_is_reported():
    r = call(generate_donation_record, **BASE)
    assert any("training" in g for g in r["compliance_gaps"])


def test_a_fully_documented_donation_has_no_gaps():
    r = call(generate_donation_record, **BASE,
             handler_name="A. Chen", handler_training_date="2026-03-14",
             written_agreement_ref="AGR-2026-014")
    assert r["complete"] is True
    assert r["compliance_gaps"] == []


def test_unknown_recipient_is_rejected():
    r = call(generate_donation_record, **{**BASE, "recipient_id": "REC-NOPE"})
    assert "error" in r


def test_malformed_items_are_rejected_rather_than_counted_as_zero():
    r = call(generate_donation_record, **{**BASE, "items_json": "not json"})
    assert "error" in r


def test_monthly_summary_totals_pounds_per_recipient():
    a = call(generate_donation_record, **BASE)
    b = call(generate_donation_record, **{**BASE,
                                          "donated_at": "2026-09-20T10:00"})
    s = call(monthly_pounds_summary, records_json=json.dumps([a, b]))
    month = s["months"]["2026-09"]
    assert month["total_lbs"] == 72.0
    assert len(month["by_recipient"]) == 1
