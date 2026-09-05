"""End-to-end checks that need a live model.

These cost money and take minutes, so they are skipped unless KSA_LIVE=1.
They assert *behaviour*, never wording: a model swap is expected to change
the prose and must not change any of these conclusions.

    KSA_LIVE=1 .venv/bin/python -m pytest tests/test_pipeline_live.py -v
"""

from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

pytestmark = pytest.mark.skipif(
    os.getenv("KSA_LIVE") != "1",
    reason="live model run; set KSA_LIVE=1 to enable",
)

CLOSED_AT = "2026-09-05T21:30"


@pytest.fixture(scope="module")
def run() -> dict[str, object]:
    """Run the pipeline once and share the result across all checks."""
    from kitchen_surplus.agents import build_orchestrator
    from kitchen_surplus.llm import active_provider, resolve_model_id

    agent = build_orchestrator(quiet=True)
    answer = str(agent(
        f"The restaurant closed at {CLOSED_AT}. The end-of-day export is at "
        f"{ROOT / 'data' / 'pos_eod_sample.csv'}. Work out what to do with "
        f"tonight's surplus."
    ))
    calls = [
        block["toolUse"]["name"]
        for message in agent.messages
        for block in message.get("content", [])
        if isinstance(block, dict) and "toolUse" in block
    ]

    provider = active_provider()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    (out_dir / f"pipeline_{provider}_{stamp}.txt").write_text(
        f"provider={provider} model={resolve_model_id('reasoning', provider)}\n"
        f"tool_calls={calls}\n\n{answer}",
        encoding="utf-8",
    )
    return {"answer": answer, "calls": calls}


def test_delegates_to_both_specialist_agents(run):
    assert "safety_agent" in run["calls"]
    assert "matching_agent" in run["calls"]


def test_enumerates_recipients_instead_of_guessing_ids(run):
    """The bug that made the first run match nothing."""
    assert "list_recipients" in run["calls"]


def test_expired_item_is_discarded(run):
    answer = run["answer"].lower()
    assert "fried rice" in answer
    discard_section = answer[answer.rfind("discard"):]
    assert "fried rice" in discard_section


def test_cooling_checkpoints_are_reported_as_times(run):
    assert re.search(r"\b70\s*°?f\b", run["answer"], re.I)
    assert re.search(r"\b41\s*°?f\b", run["answer"], re.I)
    assert "23:30" in run["answer"]


def test_pickup_minimum_blocks_white_pony_express(run):
    """97.65 lb is below their published 300 lb pickup threshold."""
    answer = run["answer"]
    assert "White Pony" in answer
    assert "300" in answer


def test_food_bank_that_refuses_restaurant_food_is_not_a_placement(run):
    """SF-Marin publicly refuses restaurant food; it must not be proposed."""
    answer = run["answer"]
    match = re.search(r"(SF-?Marin|San Francisco-Marin)", answer, re.I)
    if match is None:
        return  # correctly absent
    window = answer[max(0, match.start() - 200):match.end() + 200].lower()
    assert any(w in window for w in
               ("not accept", "does not", "refuse", "exclude", "cannot")), (
        "SF-Marin appeared without an explanation of why it is excluded"
    )


def test_unpublished_constraints_are_surfaced_as_questions(run):
    answer = run["answer"].lower()
    assert "confirm" in answer or "unpublished" in answer
    assert "food runners" in answer


def test_safety_gate_conditions_the_next_day_plan(run):
    answer = run["answer"].lower()
    assert any(w in answer for w in ("assume", "gated", "conditional",
                                     "provided", "only if", "prerequisite"))
