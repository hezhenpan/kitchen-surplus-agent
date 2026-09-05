"""Read a restaurant end-of-day export into SurplusItem records."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from strands import tool

from ..models import HoldingState, SurplusItem


def _parse_dt(raw: str) -> datetime | None:
    return datetime.fromisoformat(raw) if raw else None


def _parse_temp(raw: str) -> float | None:
    return float(raw) if raw else None


def load_surplus_items(csv_path: str | Path) -> list[SurplusItem]:
    """Parse an end-of-day export, keeping only lines with leftover quantity."""
    items: list[SurplusItem] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            remaining = float(row["remaining_qty"])
            if remaining <= 0:
                continue
            items.append(
                SurplusItem(
                    item_id=row["item_id"],
                    name=row["name"],
                    menu_category=row["menu_category"],
                    station=row["station"],
                    remaining_qty=remaining,
                    unit=row["unit"],
                    unit_weight_lbs=float(row["unit_weight_lbs"]),
                    prepared_at=datetime.fromisoformat(row["prepared_at"]),
                    holding_state=HoldingState(row["holding_state"]),
                    last_temp_f=_parse_temp(row["last_temp_f"]),
                    last_temp_check_at=_parse_dt(row["last_temp_check_at"]),
                )
            )
    return items


@tool
def parse_pos_export(csv_path: str) -> str:
    """Read a restaurant's end-of-day POS export and list what is left over.

    Args:
        csv_path: Path to the end-of-day CSV export.

    Returns:
        JSON list of leftover items with weight, preparation time, holding
        state and last recorded temperature.
    """
    items = load_surplus_items(csv_path)
    payload = [
        {
            "item_id": it.item_id,
            "name": it.name,
            "menu_category": it.menu_category,
            "weight_lbs": it.weight_lbs,
            "prepared_at": it.prepared_at.isoformat(),
            "holding_state": it.holding_state.value,
            "last_temp_f": it.last_temp_f,
            "last_temp_check_at": (
                it.last_temp_check_at.isoformat() if it.last_temp_check_at else None
            ),
        }
        for it in items
    ]
    return json.dumps(payload, indent=2)
