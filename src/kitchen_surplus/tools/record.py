"""Donation records required of a commercial edible food generator.

Field set follows Cal. Code Regs. tit. 14, s 18991.4. A generator must keep:

  - a list of each food recovery service or organization it donates to
  - a copy of the contract or written agreement with each
  - the name, address and contact information for each
  - the quantity of edible food recovered, in pounds per month
  - records that a safe food handling and storage training programme is in
    place, showing employee name, date and signature

Two of those -- the agreement and the training record -- are things the
restaurant already has or does not. The tool records the reference, and says
so plainly when the reference is missing, because an incomplete record is a
compliance gap the manager needs to see rather than a field to leave blank.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime

from strands import tool

from .recipients import load_recipients

CITATION = "Cal. Code Regs. tit. 14, s 18991.4"


@tool
def generate_donation_record(
    generator_name: str,
    generator_address: str,
    recipient_id: str,
    donated_at: str,
    items_json: str,
    handler_name: str | None = None,
    handler_training_date: str | None = None,
    written_agreement_ref: str | None = None,
) -> str:
    """Produce the record a California edible food generator must keep.

    Args:
        generator_name: Legal name of the donating business.
        generator_address: Street address of the donating business.
        recipient_id: Recipient identifier from data/recipients.json.
        donated_at: ISO timestamp of the handoff.
        items_json: JSON list of {"name": str, "weight_lbs": float} donated.
        handler_name: Employee who handled the donation.
        handler_training_date: Date that employee completed food safety
            training, ISO format.
        written_agreement_ref: Reference to the contract or written agreement
            with this recipient.

    Returns:
        JSON record with the required fields, plus `compliance_gaps` naming
        anything the regulation requires that was not supplied.
    """
    recipient = next(
        (r for r in load_recipients() if r.recipient_id == recipient_id), None
    )
    if recipient is None:
        return json.dumps({"error": f"unknown recipient_id {recipient_id}"})

    try:
        items = json.loads(items_json)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"items_json is not valid JSON: {exc}"})

    donated = datetime.fromisoformat(donated_at)
    pounds = round(sum(float(i["weight_lbs"]) for i in items), 2)

    gaps: list[str] = []
    if not written_agreement_ref:
        gaps.append(
            f"No written agreement on file with {recipient.name}. "
            f"{CITATION} requires a contract or written agreement with each "
            f"food recovery organization, and a copy kept on file."
        )
    if not handler_name or not handler_training_date:
        gaps.append(
            f"No food safety training record for the handling employee. "
            f"{CITATION} requires training records showing employee name, "
            f"date and signature."
        )

    record = {
        "record_id": f"KSA-{donated:%Y%m%d-%H%M}-{recipient_id}",
        "citation": CITATION,
        "generator": {"name": generator_name, "address": generator_address},
        "recipient": {
            "recipient_id": recipient.recipient_id,
            "name": recipient.name,
            "address": recipient.address,
            "contact_email": recipient.contact_email,
            "contact_phone": recipient.contact_phone,
        },
        "donated_at": donated.isoformat(),
        "reporting_month": f"{donated:%Y-%m}",
        "pounds_donated": pounds,
        "food_types": sorted({str(i["name"]) for i in items}),
        "line_items": [
            {"name": i["name"], "weight_lbs": float(i["weight_lbs"])}
            for i in items
        ],
        "written_agreement_ref": written_agreement_ref,
        "handler": {
            "name": handler_name,
            "training_date": handler_training_date,
            "signature": None,
        },
        "compliance_gaps": gaps,
        "complete": not gaps,
    }
    return json.dumps(record, indent=2)


@tool
def monthly_pounds_summary(records_json: str) -> str:
    """Total pounds donated per recipient per month.

    Args:
        records_json: JSON list of records from generate_donation_record.

    Returns:
        JSON summary keyed by reporting month, as the pounds-per-month figure
        the regulation asks the generator to keep.
    """
    try:
        records = json.loads(records_json)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"records_json is not valid JSON: {exc}"})

    totals: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for record in records:
        month = record["reporting_month"]
        name = record["recipient"]["name"]
        totals[month][name] += float(record["pounds_donated"])

    return json.dumps({
        "citation": CITATION,
        "months": {
            month: {
                "by_recipient": {n: round(p, 2) for n, p in by_name.items()},
                "total_lbs": round(sum(by_name.values()), 2),
            }
            for month, by_name in sorted(totals.items())
        },
    }, indent=2)
