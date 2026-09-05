# Devpost submission copy

Track: **Good Neighbor Agents**

---

## Tagline (one line)

The twenty minutes of unpaid work before a food-donation app can help you.

---

## Description

### The problem

A restaurant closes at 21:30 with a hundred pounds of good food on the pass.
It goes in the bin — not because nobody cares, but because donating it costs
about twenty minutes of unpaid work after close: deciding what is still safe to
give away, weighing it, writing it up, and finding someone who will take it.
The research on why restaurants don't donate is consistent about this: staff
must sort salvageable food, weigh and log it, and coordinate pickup, and that
labour happens outside service hours, on overtime.

In California this is no longer optional. Under SB 1383, Tier 2 commercial
edible food generators — restaurants with 250 or more seats or 5,000+ sq ft,
plus hotels, caterers and food service providers — must arrange edible food
recovery and keep records of it: pounds recovered per month, a written
agreement with each recovery organization, and staff food-safety training
records (14 CCR 18991.4). Most kitchens do this on paper, or not at all.

### Who this is for

The manager of a mid-size or large restaurant, hotel kitchen or catering
operation covered by SB 1383 — and, downstream, the food recovery
organizations that would rather receive a clean, labelled, safety-checked
donation than a phone call at eleven at night.

### What it does

Kitchen Surplus Agent reads the end-of-day POS export and, in the fifteen
minutes after close, produces three things:

1. **Tonight's checklist** — which pans go into rapid cooling, in what order,
   with the temperature checkpoints and the times they are due.
2. **Tomorrow's plan** — where each item is going, who to contact, and what
   still has to be confirmed with the organization because they have not
   published it.
3. **The compliance record** — the fields 14 CCR 18991.4 requires, and an
   explicit list of what is missing when the record is not complete.

### What makes this different

Careit and Copia already solve what happens *after* a surplus post exists:
matching, pickup logistics, donation logs. Careit is free and generates the
SB 1383 written agreement. But every one of these platforms begins with a human
creating the post — specifying type, weight, condition and pickup details.
Nobody automates the twenty minutes before it. This project sits upstream of
them and feeds them; it is not a competitor to the food recovery network.

### The thing the data taught us

Filling the recipient list with four real Bay Area organizations, transcribed
from their own public donor pages, and running the clock against a Saturday
close, the constraints collide:

```
Restaurant closes                    21:30 Sat
Hot food's safe window ends         ~01:30 Sun    (FDA Food Code 3-501.19)

Food Runners SF      hours not published on their donor page
White Pony Express   opens 08:00 Sun  — 10.5 h away, needs 300 lb for pickup
SF-Marin Food Bank   opens 08:00 Mon  — and refuses restaurant food outright
Alameda County CFB   opens 07:00 Mon  — 33.5 h away
```

At the moment the surplus appears, nothing is open, and by the time anything
is, the hot food is no longer safe to give. That is the mechanism by which this
food is wasted — and it means the decisive action is not matching. It is
deciding, tonight, which pans go into rapid cooling, converting a four-hour hot
clock into a cold donation that survives to morning.

### How it is built

Three Strands agents in an agents-as-tools arrangement — an orchestrator, a
Safety Agent with veto power over any plan, and a Matching Agent — over six
deterministic tools. One rule governs the split:

> **Judgement goes to an agent. Arithmetic goes to a tool.**

Whether "Kung Pao Chicken" is a temperature-controlled food is a judgement
about a free-text menu name; an agent decides that. How long it then stays safe
is arithmetic against the FDA Food Code; a tool decides that, and the Safety
Agent is instructed never to state a deadline it did not get back from one.
Every threshold in the rule set carries its source. The model classifies; it
does not invent limits.

A typical run makes 44 tool calls: the Safety Agent evaluates all eleven
leftover lines and builds six cooling plans, the Matching Agent enumerates
recipients and runs a nineteen-pairing eligibility matrix, and the orchestrator
returns to matching twice after the safety verdicts land.

### Two bugs the build found

**The agent could look recipients up but not list them.** Its tools were keyed
by recipient id and nothing enumerated them. It guessed seventeen identifier
formats, matched nothing — and then reported plainly that it had placed
nothing rather than inventing an organization. The guardrail held; the tool
surface was the bug.

**The cooling tool granted time the law does not allow.** FDA 3-501.14 gives
six hours to cool cooked food, but that assumes food leaving the stove above
135°F. Applied to a pan already sitting at 96°F — which had spent 1.5 of its
4 danger-zone hours — it offered the full six. The model noticed and reasoned
around it. That is the wrong place for the fix, so the rule moved into the
tool, with a test.

### On the data

All POS data is synthetic and vendor-neutral; no merchant data is used.
Recipient constraints are transcribed from each organization's own public donor
page with the source URL recorded. A constraint an organization does not
publish is stored as null, and the agent is required to treat that as something
to ask about rather than assume — which is why a run ends with a short list of
questions for the recipient rather than a fabricated certainty.

### Testing

20 unit tests cover the deterministic layer with no model in the loop. A
separate live suite asserts behaviour rather than wording — that the expired
item is discarded, that the 300 lb pickup minimum blocks a placement, that a
food bank which refuses restaurant food never becomes a destination, that
unpublished constraints surface as questions. A model swap is expected to
change the prose and must not change any of those conclusions.

### Limitations

Recipient constraints are a snapshot and are not re-fetched. Routing is not
solved — drop-off versus pickup is decided, distance is not. Nothing is
dispatched: the agent produces the handoff, a human sends it. Coverage is four
Bay Area organizations, enough to exercise the constraint types, not enough to
serve a real kitchen.

---

## Standard Devpost sections

**Inspiration** — I set out to build a surplus matching engine. Two hours of
research killed it: Careit and Copia already do that, and Careit is free. But
reading how they work, every one of them starts with a human posting the food.
The twenty minutes before that post is the part nobody automates, and it is
exactly the part that is unpaid, after hours, and full of judgement calls.

**What it does** — see the description above.

**How we built it** — Strands Agents SDK, three agents in an agents-as-tools
arrangement over six deterministic tools; food safety rules in a sourced YAML
rule set; recipient constraints transcribed from public donor pages; Streamlit
front end. The model provider sits behind a factory so Bedrock, the Anthropic
API and a local model are a config change.

**Challenges** — The interesting one was epistemic: deciding what the model is
allowed to decide. The first version let the agent reason about time limits and
it was plausible and unverifiable. Moving every threshold into a sourced tool
and forbidding the agent from stating an uncomputed deadline is what makes the
output auditable.

**Accomplishments** — The output is something a tired manager could actually
act on at 21:30: a prioritised cooling checklist with times, one phone call for
tomorrow, four specific questions, and a compliance record that names its own
gaps.

**What we learned** — Spend the first hours on constraints, not code. The best
design decision here came from reading four donor pages and noticing the hours
did not overlap with a restaurant's close. And leave null fields null: the runs
that end with "here are four things to confirm" are the ones a kitchen could
use.

**What's next** — Re-fetch recipient constraints on a schedule; route and
distance; a handoff into Careit's API rather than a phone call; more than four
organizations.

---

## Built with

`python` · `strands-agents` · `streamlit` · `pytest` · `pyyaml`

> Add `amazon-bedrock` and `amazon-bedrock-agentcore` **only if the final
> submission actually runs on them.** Do not tag what you did not use.

## Try it out

- GitHub: https://github.com/hezhenpan/kitchen-surplus-agent
