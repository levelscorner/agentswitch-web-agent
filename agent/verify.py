"""Verify -> refine (S17).

Prefer reality: re-read the DB and confirm the agent's work actually landed.
Fall back to an LLM judge only for fuzzy quality that has no hard ground truth.
`run_verify` is the DAG node that runs after the goal nodes and writes the verdict.
"""
from agent import config, llm


def _list(client, name, args):
    r = client.call(name, args)
    return r if isinstance(r, list) else r.get("items", r.get("data", r.get("results", [])))


def _orphans(client):
    wid = config.WEBSITE_SURYODAYA
    pages = _list(client, "Webpage.list", {"website_id": wid, "limit": 200})
    menus = _list(client, "WebsiteMenu.list", {"website_id": wid, "limit": 200})
    blob = str(menus).lower()
    return {p.get("id") for p in pages
            if p.get("status") == "published" and (p.get("slug") or "").lower() not in blob}


def reality_check(client, state):
    """Per-goal ground-truth check. Returns {ok, goals: {g: {ok, note}}}."""
    goals = state.get("goals", [])
    out = {}
    if "publish" in goals:
        posts = _list(client, "BlogPost.list", {"limit": 200})
        live = any(p.get("status") == "published" and "fixture" in (p.get("title") or "").lower()
                   for p in posts)
        out["publish"] = {"ok": live, "note": "published fixture post found" if live
                          else "no published fixture post"}
    if "dead_pages" in goals:
        want = _orphans(client)
        got = {p.get("id") for p in state.get("dead_pages", [])}
        ok = bool(got) and got == want
        out["dead_pages"] = {"ok": ok, "note": f"agent={len(got)} db={len(want)} match={ok}"}
    if "refuse" in goals:
        refused = bool(state.get("refused"))
        out["refuse"] = {"ok": refused, "note": "refused" if refused else "did not refuse"}
    return {"ok": all(v["ok"] for v in out.values()) if out else True, "goals": out}


def judge(client, text, rubric, tier="hard"):
    """LLM-as-judge for fuzzy quality with no hard ground truth (S17 fallback)."""
    data = llm.draft_json(
        'You are a strict grader. Return JSON {"ok": true|false, "why": "..."}.',
        f"Rubric: {rubric}\n\nText:\n{text}", tier=tier, max_tokens=200)
    return bool(data.get("ok")), data.get("why", "")


def run_verify(client, state):
    """DAG node: read reality, write the verdict onto the blackboard."""
    state["verify"] = reality_check(client, state)
