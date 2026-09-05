# Agents for Humans: the twenty minutes before the food-donation app

*Draft for builder.aws.com — title must contain "Agents for Humans" to
qualify for the hackathon bonus, and it must be published before the
submission deadline.*

---

I started this build expecting to write a matching engine. Restaurants have
surplus, food banks need food, an agent connects them. Two hours of research
killed that idea, and the thing that replaced it is better.

## The idea was already taken, and that was useful

Careit and Copia already do surplus matching. Careit is free, generates the
SB 1383 written agreement automatically, and produces audit-ready donation
reports. If your pitch is "an agent that logs food donations", theirs is
shipped and yours is a demo.

But read how they work: *the business creates a post specifying the type,
weight, condition and pickup details.* A human does that. And the industry
research on why restaurants don't donate is unambiguous about what that human
is actually doing — sorting salvageable food, weighing and logging it,
coordinating pickup, after close, on overtime.

Nobody automates the twenty minutes before the post. That is where an agent
belongs.

## Then the data told me what the real problem was

I filled the recipient list with four real Bay Area organizations, transcribing
constraints from their own donor pages: what they accept, opening hours,
minimum quantities. Then I ran the clock against a Saturday close.

Everything was shut. The restaurant closes at 21:30. The hot food is safe for
four hours. The nearest organization opens 10.5 hours later; the food banks,
33.5 hours later. At the moment the surplus exists, there is no one to give it
to, and by the time there is, it is no longer safe to give.

That reframed the product. The valuable action is not matching. It is deciding,
in the fifteen minutes after close, which pans go into rapid cooling — turning a
four-hour hot clock into a cold donation that survives until morning.

## Judgement to the agent, arithmetic to the tool

Whether "Kung Pao Chicken" is a temperature-controlled food is a judgement about
a free-text menu name. How long it then stays safe is arithmetic against the FDA
Food Code. I split those: the Safety Agent classifies, and a deterministic tool
computes, with the agent instructed never to state a deadline it did not get
back from that tool.

Two failures made the case for the split better than I could have.

**The agent could look recipients up but not list them.** Its tools were keyed
by `recipient_id` and nothing enumerated them. It guessed seventeen identifier
formats, matched nothing — and then reported plainly that it had placed nothing,
rather than inventing an organization to fill the gap. The guardrail worked. The
tool surface was the bug.

**My cooling tool granted time the law does not allow.** FDA 3-501.14 gives you
six hours to cool cooked food, but that assumes food leaving the stove above
135°F. One pan had been sitting at 96°F for ninety minutes, spending a
danger-zone clock that cooling does not reset. The tool cheerfully offered the
full six hours. The model noticed and reasoned around it.

That is the wrong place for the fix. A model that catches your bug today may
trust your tool tomorrow. The rule moved into the tool, with a test.

## What I would tell someone starting this week

Spend the first two hours on the constraints, not the code. My best design
decision came from reading four donor pages and noticing that the hours did not
overlap with a restaurant's close. No amount of prompt engineering would have
produced that.

And leave the null fields null. When an organization does not publish its
pickup window, the honest output is a question, not a confident guess. The runs
that end with "here are four things to confirm with them" are the ones a real
kitchen could act on.

*Code: github.com/hezhenpan/kitchen-surplus-agent (MIT)*
