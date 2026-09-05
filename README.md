# Kitchen Surplus Agent

An agent that turns a restaurant's end-of-day POS export into a donation-ready,
compliance-ready surplus handoff — before anyone has to think about it.

> Status: work in progress. Built for the AWS *Agents for Humans* hackathon.

## The problem

Restaurants do not skip food donation because they don't care. They skip it
because donating costs roughly twenty minutes of unpaid, after-close judgement
work: sorting what is still safe, weighing it, deciding whether prepared food
can legally leave the building, describing it, and then keeping the records the
law requires.

In California, that work is no longer optional. Under SB 1383, Tier 2
commercial edible food generators — restaurants with 250+ seats or 5,000+
sq ft, plus hotels, caterers and food service providers — must arrange edible
food recovery and keep records of it (14 CCR 18991.4).

## What this is not

Platforms like Careit and Copia already solve what happens *after* a surplus
post exists: matching, pickup logistics and donation logs. This project sits
**upstream of them**. It produces the post — with weights, safety windows and
labels already worked out — and hands it off. It is a feeder for the food
recovery network, not a competitor to it.

## How it works

- **Safety Agent** classifies each leftover line as TCS or non-TCS and holds
  veto power over any proposed match.
- **Matching Agent** fits items to recipients under real intake constraints
  (hours, refrigeration, capacity, dietary restrictions), splitting a donation
  across recipients when no single one can take it.
- Deterministic tools handle everything that must not be improvised: the
  time/temperature clock, the donation record, the required labels.

Food safety thresholds are enforced from `rules/tcs_rules.yaml`, where every
value carries its source. The model classifies; it does not invent limits.

## Data

All POS data in this repository is synthetic and vendor-neutral
(`scripts/gen_pos_data.py`). No real merchant data is used.

## License

MIT
