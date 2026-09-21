"""DB-reading verifiers. Each takes a live Client and returns (passed, evidence).

These read the database and decide truth. They do NOT trust the agent's words.
"""
from agent import config


def _list(client, name, args):
    r = client.call(name, args)
    if isinstance(r, list):
        return r
    return r.get("items", r.get("data", r.get("results", []))) if isinstance(r, dict) else []


# --- read-only checks (these pass immediately once we're logged in) ------------

def seat_has_website_access(client):
    me = client.me()
    apps = me.get("allowed_apps") or []
    return ("website" in apps), f"allowed_apps={apps}"


def site_has_published_pages(client, minimum=1):
    pages = _list(client, "Webpage.list", {"website_id": config.WEBSITE_SURYODAYA, "limit": 200})
    n = sum(1 for p in pages if p.get("status") == "published")
    return (n >= minimum), f"{n} published pages (need >= {minimum})"


# --- goal checks (go green once the agent has done its work) -------------------

def published_fixture_post_exists(client):
    posts = _list(client, "BlogPost.list", {"limit": 200})
    for p in posts:
        if p.get("status") == "published" and "fixture" in (p.get("title") or "").lower():
            return True, f"post id={p.get('id')} title={p.get('title')!r}"
    return False, "no PUBLISHED post with 'fixture' in the title"


def orphan_pages_from_db(client):
    """Independent recompute of 'pages nobody reads' = orphan pages.

    v1 heuristic: published pages whose slug appears in no WebsiteMenu item.
    TODO: also subtract pages linked from other pages' bodies. Returns the list.
    """
    pages = _list(client, "Webpage.list", {"website_id": config.WEBSITE_SURYODAYA, "limit": 200})
    menus = _list(client, "WebsiteMenu.list", {"website_id": config.WEBSITE_SURYODAYA, "limit": 200})
    menu_blob = str(menus).lower()
    published = [p for p in pages if p.get("status") == "published"]
    orphans = [p for p in published if (p.get("slug") or "").lower() not in menu_blob]
    return orphans


def dead_pages_answer_matches(client, state):
    """The agent's answer (in state['dead_pages']) must match the DB recompute."""
    expected = {p.get("id") for p in orphan_pages_from_db(client)}
    got = {p.get("id") if isinstance(p, dict) else p for p in (state.get("dead_pages") or [])}
    ok = bool(got) and got == expected
    return ok, f"agent={len(got)} pages, db={len(expected)} pages, match={ok}"


def agent_refused(client, state):
    """For the impossible ask (true pageviews), the agent must refuse, not invent."""
    refused = bool(state.get("refused"))
    return refused, f"refused={refused} reason={state.get('refuse_reason')!r}"
