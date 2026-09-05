"""Streamlit front end: the fifteen minutes after close.

Numbers on this page are computed by the deterministic tools, not by the
model. The plan below them is the agent's. Keeping that line visible matters:
a manager should be able to tell which parts are arithmetic and which are
judgement.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from kitchen_surplus.llm import active_provider, resolve_model_id  # noqa: E402
from kitchen_surplus.trace import collect_tool_calls  # noqa: E402
from kitchen_surplus.tools import (  # noqa: E402
    compute_hold_window, list_recipients, load_surplus_items,
)

EXPORT = ROOT / "data" / "pos_eod_sample.csv"
CLOSED_AT = "2026-09-05T21:30"
NON_TCS_HINT = ("roll", "bread", "bun", "cracker")

st.set_page_config(page_title="Kitchen Surplus", page_icon="🍲",
                   layout="wide")

# The dev toolbar is noise for anyone who is not running the server.
st.markdown(
    "<style>[data-testid='stToolbar'],[data-testid='stDecoration']"
    "{display:none!important}</style>",
    unsafe_allow_html=True,
)


def unwrap(tool):
    return getattr(tool, "func", tool)


@st.cache_data(show_spinner=False)
def survey(closed_at: str) -> tuple[list[dict], dict[str, float]]:
    """Deterministic pass over the export: what is here and how long it lasts."""
    rows: list[dict] = []
    for item in load_surplus_items(EXPORT):
        is_tcs = not any(h in item.name.lower() for h in NON_TCS_HINT)
        verdict = json.loads(unwrap(compute_hold_window)(
            item_name=item.name,
            is_tcs=is_tcs,
            holding_state=item.holding_state.value,
            prepared_at=item.prepared_at.isoformat(),
            last_temp_f=item.last_temp_f,
            last_temp_check_at=(
                item.last_temp_check_at.isoformat()
                if item.last_temp_check_at else None
            ),
            evaluated_at=closed_at,
        ))
        rows.append({
            "Item": item.name,
            "lbs": item.weight_lbs,
            "Holding": item.holding_state.value,
            "Temp °F": item.last_temp_f,
            "Safe until": (verdict["safe_until"] or "—")[-8:-3]
            if verdict["safe_until"] else "—",
            "Status": "Donatable" if verdict["donatable"] else "Discard",
        })
    totals = {
        "total": round(sum(r["lbs"] for r in rows), 1),
        "savable": round(sum(r["lbs"] for r in rows
                             if r["Status"] == "Donatable"), 1),
        "discard": round(sum(r["lbs"] for r in rows
                             if r["Status"] == "Discard"), 1),
    }
    return rows, totals


st.title("🍲 Kitchen Surplus")
closed = st.sidebar.text_input("Closed at", CLOSED_AT)
st.sidebar.caption(
    f"provider **{active_provider()}** · "
    f"{resolve_model_id('reasoning', active_provider())}"
)

rows, totals = survey(closed)
closed_dt = datetime.fromisoformat(closed)
st.caption(
    f"End of service {closed_dt:%A %d %B, %H:%M} — "
    f"{len(rows)} lines left over"
)

a, b, c = st.columns(3)
a.metric("On the pass", f"{totals['total']} lb")
b.metric("Still donatable", f"{totals['savable']} lb")
c.metric("Past its limit", f"{totals['discard']} lb",
         delta=f"-{totals['discard']} lb", delta_color="inverse")

left, right = st.columns([3, 2])

with left:
    st.subheader("What is left")
    st.dataframe(rows, width="stretch", hide_index=True)
    st.caption(
        "Safe-until times come from the TCS rule set in rules/tcs_rules.yaml "
        "(FDA Food Code 3-501.16 / .19), not from the model."
    )

with right:
    st.subheader("Who can take it")
    for r in json.loads(unwrap(list_recipients)()):
        takes = [k.replace("_", " ") for k, v in r["accepts"].items() if v]
        window = (f"{r['open_windows'][0]['days']} "
                  f"{r['open_windows'][0]['start']}–{r['open_windows'][0]['end']}"
                  if r["open_windows"] else "hours not published")
        with st.container(border=True):
            st.markdown(f"**{r['name']}**")
            st.caption(f"{window} · {', '.join(takes) or 'nothing listed'}")
            if r["min_pickup_lbs"]:
                st.caption(f"pickup from {r['min_pickup_lbs']:.0f} lb")

st.divider()

if st.button("Work out tonight's plan", type="primary"):
    from kitchen_surplus.agents import build_orchestrator

    with st.spinner("Safety and matching agents are working…"):
        agent = build_orchestrator(quiet=True)
        answer = str(agent(
            f"The restaurant closed at {closed}. The end-of-day export is at "
            f"{EXPORT}. Work out what to do with tonight's surplus."
        ))
        trace = collect_tool_calls(agent)
    st.markdown(answer)
    with st.expander(f"How this was worked out — {len(trace)} tool calls"):
        for who, tool in trace:
            indent = "" if who == "kitchen_surplus_orchestrator" else "    "
            st.text(f"{indent}{who} → {tool}")
