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
class OpenWindow:
    """A published intake window, e.g. Mon-Fri 08:00-14:00."""

    days: str
    start: str
    end: str
    note: str | None = None


@dataclass(frozen=True)
class Recipient:
    """A food recovery organization or service.

    Constraints are transcribed from each organization's own public donor
    page; `source_url` records which one. A constraint the organization does
    not publish stays `None` -- the agent must treat that as "ask", never as
    "assume yes".
    """

    recipient_id: str
    name: str
    org_type: str
    address: str
    service_area: list[str]
    contact_email: str | None
    contact_phone: str | None
    open_windows: list[OpenWindow] | None
    accepts: dict[str, bool]
    min_pickup_lbs: float | None
    offers_pickup: bool
    pickup_lead_time_minutes: int | None
    has_refrigerated_transport: bool | None
    constraints_notes: str
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
