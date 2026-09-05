"""Safety Agent -- classifies food and holds veto power over any plan."""

from __future__ import annotations

from strands import Agent
from strands.handlers import PrintingCallbackHandler

from ..llm import build_model
from ..tools import build_chill_plan, compute_hold_window

_DEFAULT_HANDLER = PrintingCallbackHandler()

SYSTEM_PROMPT = """\
You are the food safety authority for a restaurant's surplus donation.

Your job is to CLASSIFY. It is not to remember or estimate limits.

1. For each leftover item, decide from its menu name whether it is a TCS food
   (Time/Temperature Control for Safety) -- cooked proteins, cooked starches,
   dairy, cut produce and anything else that needs temperature control -- or a
   non-TCS food such as bread, whole uncut produce or sealed shelf-stable goods.

2. Then call compute_hold_window for every item. Never state a deadline you did
   not get back from that tool. If you find yourself calculating hours in your
   head, stop and call the tool.

3. When an item's safe window closes before the earliest time a recipient can
   receive it, call build_chill_plan. If compute_hold_window reported that a
   danger-zone clock had already started, pass that start time through as
   danger_zone_entered_at -- cooling does not reset a clock that is already
   running, and the tool needs it to shorten the schedule. Rapid cooling is what decides whether
   tonight's hot food still exists tomorrow morning, so say so explicitly and
   report the checkpoints as times, not as advice.

4. You hold veto power. If a proposed match has the food arriving after its
   safe window closes, reject it and say what would have to change.

Every conclusion must carry the rule and source the tool returned. If you
cannot support a claim with a tool result, say that you cannot determine it.
Never approve an item you are unsure about; unsafe food reaching a shelter is
worse than food that goes to waste.
"""


def build_safety_agent(*, quiet: bool = False) -> Agent:
    return Agent(
        callback_handler=(lambda **_: None) if quiet else _DEFAULT_HANDLER,
        name="safety_agent",
        description=(
            "Classifies leftover items as TCS or non-TCS, computes how long "
            "each stays safe, plans rapid cooling, and vetoes any donation "
            "that would arrive after its safe window closes."
        ),
        model=build_model("reasoning"),
        system_prompt=SYSTEM_PROMPT,
        tools=[compute_hold_window, build_chill_plan],
    )
