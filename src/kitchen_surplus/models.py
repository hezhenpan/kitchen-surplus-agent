"""Core domain types.

Field names for DonationRecord follow California 14 CCR 18991.4 (recordkeeping
requirements for commercial edible food generators). See rules/tcs_rules.yaml
for the food-safety thresholds referenced by HoldingState / SafetyVerdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class HoldingState(str, Enum):
    """How an item was held between preparation and end of service."""

    HOT = "hot"          # hot-holding line, expected >= 135F
    COLD = "cold"        # refrigerated, expected <= 41F
    AMBIENT = "ambient"  # room temperature -- danger zone for TCS foods


@dataclass(frozen=True)
class SurplusItem:
    """One leftover line from an end-of-day POS / prep report."""

    item_id: str
    name: str
    menu_category: str
    station: str
    remaining_qty: float
    unit: str
    unit_weight_lbs: float
    prepared_at: datetime
    holding_state: HoldingState
    last_temp_f: float | None
    last_temp_check_at: datetime | None

    @property
    def weight_lbs(self) -> float:
        return round(self.remaining_qty * self.unit_weight_lbs, 2)


@dataclass(frozen=True)
class Recipient:
    """A food recovery organization or service.

    `source_url` records where the intake constraints came from, so the demo
    data stays auditable rather than invented.
    """

    recipient_id: str
    name: str
    address: str
    contact_email: str
    contact_phone: str
    open_windows: list[str]          # e.g. ["Mon-Fri 09:00-17:00"]
    has_refrigeration: bool
    accepts_prepared_food: bool
    max_intake_lbs: float
    dietary_restrictions: list[str]  # e.g. ["no-pork", "halal-preferred"]
    source_url: str


@dataclass(frozen=True)
class SafetyVerdict:
    """Result of evaluating one item against the TCS rule set."""

    item_id: str
    is_tcs: bool
    donatable: bool
    safe_until: datetime | None
    reason: str
    required_labels: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class DonationRecord:
    """Record fields required of a commercial edible food generator.

    Source: Cal. Code Regs. tit. 14, s 18991.4.
    """

    record_id: str
    generator_name: str
    generator_address: str
    recipient_name: str
    recipient_address: str
    recipient_contact: str
    donated_at: datetime
    pounds_donated: float
    food_types: list[str]
    written_agreement_ref: str
    handler_name: str
    handler_training_date: str
