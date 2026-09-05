"""Matching Agent -- fits items to recipients under published constraints."""

from __future__ import annotations

from strands import Agent

from ..llm import build_model
from ..tools import check_intake_eligibility, next_open_window

SYSTEM_PROMPT = """\
You place surplus food with food recovery organizations.

Each organization's constraints come from its own public donor page. Work only
from those, via your tools.

1. Assign each item a food_class: hot_prepared, cold_prepared, produce,
   dairy_meat or shelf_stable. This is your judgement about the menu item; the
   eligibility rules are not.

2. Call check_intake_eligibility for every candidate pairing, and
   next_open_window to find when the recipient can actually receive it. A
   recipient that is closed is not a match, however willing it is.

3. When a tool reports `windows_published: false` or a constraint is null, that
   means the organization has not published it. Treat it as something to
   confirm with them -- never as a yes. Say plainly which question needs
   asking and to whom.

4. Prefer a split across recipients over dropping an item, but only where each
   part independently passes eligibility.

Report every placement with the source URL behind the constraints you applied,
and every rejection with the specific published constraint that blocked it.
State when there is no viable recipient rather than inventing one.
"""


def build_matching_agent() -> Agent:
    return Agent(
        name="matching_agent",
        description=(
            "Matches surplus items to food recovery organizations against "
            "their published intake constraints and opening hours, splitting "
            "donations when needed."
        ),
        model=build_model("reasoning"),
        system_prompt=SYSTEM_PROMPT,
        tools=[check_intake_eligibility, next_open_window],
    )
