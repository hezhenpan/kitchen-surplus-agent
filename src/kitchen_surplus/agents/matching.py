"""Matching Agent -- fits items to recipients under published constraints."""

from __future__ import annotations

from strands import Agent
from strands.handlers import PrintingCallbackHandler

from ..llm import build_model
from ..tools import check_intake_eligibility, list_recipients, next_open_window

_DEFAULT_HANDLER = PrintingCallbackHandler()

SYSTEM_PROMPT = """\
You place surplus food with food recovery organizations.

Each organization's constraints come from its own public donor page. Work only
from those, via your tools.

1. Start by calling list_recipients. That is where recipient identifiers
   come from -- never guess one.

2. Assign each item a food_class: hot_prepared, cold_prepared, produce,
   dairy_meat or shelf_stable. This is your judgement about the menu item; the
   eligibility rules are not.

3. Call check_intake_eligibility for every candidate pairing, and
   next_open_window to find when the recipient can actually receive it. A
   recipient that is closed is not a match, however willing it is.

4. When a tool reports `windows_published: false` or a constraint is null, that
   means the organization has not published it. Treat it as something to
   confirm with them -- never as a yes. Say plainly which question needs
   asking and to whom.

5. Prefer a split across recipients over dropping an item, but only where each
   part independently passes eligibility.

Report every placement with the source URL behind the constraints you applied,
and every rejection with the specific published constraint that blocked it.
State when there is no viable recipient rather than inventing one.
"""


def build_matching_agent(*, quiet: bool = False) -> Agent:
    return Agent(
        callback_handler=(lambda **_: None) if quiet else _DEFAULT_HANDLER,
        name="matching_agent",
        description=(
            "Matches surplus items to food recovery organizations against "
            "their published intake constraints and opening hours, splitting "
            "donations when needed."
        ),
        # This agent reports a full item-by-recipient eligibility matrix, which
        # overran a 4k budget and left the orchestrator retrying a truncated
        # response until it gave up.
        model=build_model("reasoning", max_tokens=16384),
        system_prompt=SYSTEM_PROMPT,
        tools=[list_recipients, check_intake_eligibility, next_open_window],
    )
