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


def _rows(client, name, args):
    r = client.call(name, args)
    if isinstance(r, list):
        return r
    return r.get("items", r.get("data", r.get("results", []))) if isinstance(r, dict) else []


def _own_open_escalation(rows, subject):
    closed = {"resolved", "closed", "cancelled", "withdrawn"}
    for r in rows:
        if (r.get("subject") or "") == subject and (r.get("status") or "").lower() not in closed:
            return r
    return None


def _own_session(rows, created_by, title):
    """Our own AgentSession (we created it, carries our marker title) — never another team's."""
    for s in rows:
        if s.get("created_by") == created_by and (s.get("title") or "") == title:
            return s
    return None


def _ensure_session(client):
    """Reuse our marker session if present, else create one. Escalations attach to this."""
    title = config.AGENT_SESSION_TITLE
    me_id = client.me().get("id")
    mine = _own_session(_rows(client, "AgentSession.list", {"limit": 200}), me_id, title)
    if mine:
        return mine.get("id")
    created = client.call("AgentSession.create",
                          {"title": title, "channel": "api"})
    return (created or {}).get("id")


def run_refusal(client, state):
    """Impossible ask: 'exact view count for every page.' The platform tracks no per-page
    readership (Webpage carries no view field), so the honest answer is to REFUSE — not
    invent numbers. Read-only: refusing is a judgement, not a write.

    (We briefly raised an AgentEscalation here, but Release 8.1 removed AgentEscalation.create
    from this seat's grant, so the refusal is now verified purely from the DB — see
    harness/verifiers.agent_refused.)"""
    state["refused"] = True
    state["refuse_reason"] = ("AgentSwitch tracks no per-page view/visitor counts (Webpage has "
                              "no view field), so exact readership numbers cannot be produced. "
                              "I can instead return orphan / unreachable pages and say so honestly.")
