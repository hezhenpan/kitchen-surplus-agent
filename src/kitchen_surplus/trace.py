"""Collect tool calls across an orchestrator and its sub-agents.

An agent used as a tool keeps its own message history, so the calls it makes
never appear in the orchestrator's. Anything inspecting a run -- a regression
test, the UI's trace panel -- has to walk into them.
"""

from __future__ import annotations

from strands import Agent


def _own_calls(agent: Agent) -> list[str]:
    return [
        block["toolUse"]["name"]
        for message in agent.messages
        for block in message.get("content", [])
        if isinstance(block, dict) and "toolUse" in block
    ]


def _sub_agents(agent: Agent) -> list[tuple[str, Agent]]:
    registry = getattr(getattr(agent, "tool_registry", None), "registry", {})
    out: list[tuple[str, Agent]] = []
    for name, tool in registry.items():
        inner = getattr(tool, "agent", None)
        if isinstance(inner, Agent):
            out.append((name, inner))
    return out


def collect_tool_calls(agent: Agent) -> list[tuple[str, str]]:
    """Every tool call in a run, as (agent name, tool name), in order.

    Sub-agent calls follow the delegation that triggered them, so the result
    reads as the shape of the run rather than a flat set.
    """
    label = agent.name or "agent"
    calls: list[tuple[str, str]] = []
    subs = dict(_sub_agents(agent))
    for tool_name in _own_calls(agent):
        calls.append((label, tool_name))
        if tool_name in subs:
            calls.extend(collect_tool_calls(subs.pop(tool_name)))
    # A sub-agent invoked more than once has already contributed its whole
    # history above; anything never invoked contributes nothing.
    return calls


def tool_names(agent: Agent) -> list[str]:
    """Flat list of every tool called anywhere in the run."""
    return [tool for _, tool in collect_tool_calls(agent)]
