"""Run the surplus plan for one end-of-day export."""

from __future__ import annotations

import argparse
from pathlib import Path

from .agents import build_orchestrator
from .llm import active_provider

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--export", default=str(REPO_ROOT / "data" / "pos_eod_sample.csv"),
        help="Path to the end-of-day POS export.",
    )
    parser.add_argument(
        "--closed-at", default="2026-09-05T21:30",
        help="ISO timestamp the restaurant closed.",
    )
    args = parser.parse_args()

    print(f"provider: {active_provider()}\n")
    agent = build_orchestrator()
    agent(
        f"The restaurant closed at {args.closed_at}. The end-of-day export is "
        f"at {args.export}. Work out what to do with tonight's surplus."
    )


if __name__ == "__main__":
    main()
