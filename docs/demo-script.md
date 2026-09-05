# Demo video — shot list (target 4:30, hard limit 5:00)

Judged on Presentation: *clear end-to-end demonstration, compelling pitch
communicating problem / audience / significance, easy to follow.*

The single most important shot is **04 — the collision**. Everything before it
is setup; everything after is payoff. If you are running long, cut 06, not 04.

---

### 00:00–00:35 · The problem, said plainly
**Screen:** a plated-up pass at close, or the Streamlit metrics row.

> "A restaurant closes at half nine. There's a hundred and eleven pounds of
> good food on the pass. It won't be donated — not because nobody cares, but
> because donating it costs twenty minutes of unpaid work after close:
> deciding what's still safe, weighing it, writing it up, and finding someone
> who'll take it. So it goes in the bin."

### 00:35–01:05 · Why this is now the law
**Screen:** the SB 1383 line in the README, then 14 CCR 18991.4.

> "In California that's no longer a choice. Under SB 1383, restaurants over
> two-fifty seats have to arrange food recovery and keep records of it —
> pounds per month, a written agreement with each organization, staff training
> records. Most kitchens do that on paper, or not at all."

### 01:05–01:35 · What already exists, and where the gap is
**Screen:** Careit / Copia homepages, then your architecture diagram.

> "Careit and Copia already handle what happens after you post surplus food —
> matching, pickup, logs. Careit's free. But every one of them starts with a
> human posting the food. Nobody does the twenty minutes *before* the post.
> That's what this is."

### 01:35–02:10 · The tool, running
**Screen:** Streamlit. Point at the metrics row.

> "It reads the end-of-day POS export. A hundred and eleven pounds left,
> ninety-eight still donatable, fourteen already past its limit. Those numbers
> are computed, not guessed — the safety clock comes from the FDA Food Code,
> not from the model."

Click **Work out tonight's plan**.

### 02:10–03:00 · ⭐ The collision
**Screen:** the timing block from the README, held on screen while you talk.

> "Here's what it found, and it's the whole problem in one picture. The
> restaurant closed at half nine on a Saturday. The hot food's safe for four
> hours — gone by half one in the morning. White Pony Express opens at eight
> on Sunday: ten and a half hours away. The food banks don't open until
> Monday — thirty-three hours. At the moment this food appears, **nothing is
> open**, and by the time anything is, it's already unsafe.
>
> So the agent doesn't try to find someone to take it tonight. It works out
> what has to happen in the next fifteen minutes: which six pans go into rapid
> cooling, to turn a four-hour hot clock into a cold donation that survives
> until morning."

### 03:00–03:40 · The veto, and the catch it made
**Screen:** the TONIGHT checklist. Highlight the Mac & Cheese line.

> "The safety agent holds a veto over the whole plan. It threw out the fried
> rice — its clock ran out at half eight, before the restaurant even closed,
> and cooling can't restart an expired clock.
>
> And look at the mac and cheese. The FDA cooling schedule gives you six hours
> — but this pan has been sitting at ninety-six degrees since eight, so it's
> already spent an hour and a half of its danger-zone budget. It gets until
> midnight, not half three. My tool got that wrong. The agent caught it. I
> moved the rule into the tool and wrote a test, because next time it might
> not catch it."

### 03:40–04:15 · Tomorrow, and the honesty
**Screen:** the TOMORROW section.

> "Then it places the food. Food Runners is the only organization that takes
> prepared restaurant food. White Pony Express would, but they need three
> hundred pounds to send a van and there's ninety-eight — so that becomes a
> drop-off, not a pickup. The San Francisco food bank never comes up: their
> own page says they don't accept restaurant food.
>
> And it ends with four questions, not four assumptions — Sunday pickup,
> the window, city limits, and whether they'll take clam chowder. Those are
> the fields those organizations don't publish. It won't guess them."

### 04:15–04:30 · Close
**Screen:** the compliance record with its gaps.

> "Every claim carries the rule it came from, so the record stands up to an
> audit — and when the record isn't complete, it says which part is missing
> instead of leaving a blank. Twenty minutes of after-close work, down to a
> checklist and one phone call."

---

## Rules for the recording

- **Do not narrate the architecture.** Show the diagram for four seconds under
  the "what already exists" line. Judges read it in the README.
- **Pre-run the agent.** Do not make viewers watch a live model call. Record the
  click, cut, resume on the output.
- **Show one real citation on screen at full size** — the FDA 3-501.14 line —
  so the sourcing is visibly real, not a claim.
- **Say "I got this wrong" out loud** in the 03:00 section. It is the most
  credible thirty seconds in the whole video.
- No music under narration. No logo animation. Start on the problem.
