"""Generate a synthetic end-of-day POS / prep report.

The schema here is a generic restaurant end-of-day export -- deliberately
vendor-neutral. All data is fabricated for demonstration.

Usage:
    python scripts/gen_pos_data.py > data/pos_eod_sample.csv
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timedelta

CLOSE_TIME = datetime(2026, 9, 5, 21, 30)

COLUMNS = [
    "item_id", "name", "menu_category", "station",
    "prepared_qty", "sold_qty", "remaining_qty", "unit", "unit_weight_lbs",
    "prepared_at", "holding_state", "last_temp_f", "last_temp_check_at",
]

# (name, category, station, prepared, sold, unit, unit_wt, prep_offset_h,
#  holding, temp_f, temp_check_offset_h)
# Offsets are hours BEFORE close, so the safety clock is deterministic.
ROWS: list[tuple] = [
    ("Rotisserie Chicken",      "Entree",  "Grill",   24, 12, "each", 2.5, 3.0, "hot",     141.0, 0.5),
    ("Steamed Jasmine Rice",    "Side",    "Wok",     40, 26, "lb",   1.0, 5.5, "hot",     138.0, 0.5),
    ("Kung Pao Chicken",        "Entree",  "Wok",     30, 22, "lb",   1.0, 6.0, "hot",     129.0, 0.5),
    ("Caesar Salad (undressed)","Salad",   "Cold",    18, 11, "each", 0.6, 4.0, "cold",     38.0, 0.5),
    ("Dinner Rolls",            "Bakery",  "Bakery",  60, 41, "each", 0.15, 8.0, "ambient", None, None),
    ("Clam Chowder",            "Soup",    "Line",    25, 19, "lb",   1.0, 7.0, "hot",     144.0, 0.5),
    ("Sliced Watermelon",       "Produce", "Cold",    20, 14, "lb",   1.0, 5.0, "cold",     40.0, 0.5),
    ("Pork Belly Bao",          "Entree",  "Steam",   36, 20, "each", 0.35, 2.5, "hot",    137.0, 0.5),
    ("Garden Salad Mix (bagged)","Produce","Cold",    12,  4, "lb",   1.0, 9.0, "cold",     39.0, 0.5),
    ("Mac and Cheese",          "Side",    "Line",    28, 15, "lb",   1.0, 6.5, "ambient",  96.0, 1.5),
    ("Yangzhou Fried Rice",     "Side",    "Wok",     35, 21, "lb",   1.0, 7.0, "ambient",  88.0, 5.0),
]


def main() -> None:
    writer = csv.writer(sys.stdout)
    writer.writerow(COLUMNS)
    for i, (name, cat, station, prep, sold, unit, wt,
            prep_off, holding, temp, temp_off) in enumerate(ROWS, start=1):
        prepared_at = CLOSE_TIME - timedelta(hours=prep_off)
        check_at = CLOSE_TIME - timedelta(hours=temp_off) if temp_off is not None else ""
        writer.writerow([
            f"ITM-{i:03d}", name, cat, station,
            prep, sold, prep - sold, unit, wt,
            prepared_at.isoformat(timespec="minutes"),
            holding,
            "" if temp is None else temp,
            check_at.isoformat(timespec="minutes") if check_at else "",
        ])


if __name__ == "__main__":
    main()
