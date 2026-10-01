"""Analyst agent — Goal #2: "which pages nobody reads", plus the refusal task.

The platform records NO pageview/traffic data (conversion_attribution reads 0 across the
whole site), so we define "nobody reads" as ORPHAN PAGES: published pages not reachable
from any WebsiteMenu. We return that list AND state the definition + the honest caveat.
"""
from agent import config


def run_analyst(client, state):
    """Goal #2 now runs as a real sub-agent. This is the compatibility entry point (the
    harness and any legacy caller use it): it hands the dead_pages subgraph a scoped input
    (only website_id) and copies its scoped outputs back onto the given state."""
    from agent.subgraphs import dead_pages_subgraph   # local import avoids an import cycle
    out = dead_pages_subgraph.run(client, {"website_id": config.WEBSITE_SURYODAYA})
    state.update(out)


def run_refusal(client, state):
    """Impossible ask: 'exact view count for every page.' Correct answer is a refusal,
    because the platform stores no readership data. It must not invent numbers."""
    state["refused"] = True
    state["refuse_reason"] = ("AgentSwitch stores no per-page view/visitor counts, so exact "
                              "readership numbers cannot be produced. I can instead return "
                              "orphan / zero-conversion pages and say so honestly.")
