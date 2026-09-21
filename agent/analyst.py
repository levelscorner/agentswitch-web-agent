"""Analyst agent — Goal #2: "which pages nobody reads", plus the refusal task.

The platform records NO pageview/traffic data (conversion_attribution reads 0 across the
whole site), so we define "nobody reads" as ORPHAN PAGES: published pages not reachable
from any WebsiteMenu. We return that list AND state the definition + the honest caveat.
"""
from agent import config


def _list(client, name, args):
    r = client.call(name, args)
    return r if isinstance(r, list) else r.get("items", r.get("data", []))


def run_analyst(client, state):
    wid = config.WEBSITE_SURYODAYA
    pages = _list(client, "Webpage.list", {"website_id": wid, "limit": 200})
    menus = _list(client, "WebsiteMenu.list", {"website_id": wid, "limit": 200})
    menu_blob = str(menus).lower()

    published = [p for p in pages if p.get("status") == "published"]
    orphans = [p for p in published if (p.get("slug") or "").lower() not in menu_blob]

    state["dead_pages"] = [
        {"id": p.get("id"), "title": p.get("title"), "slug": p.get("slug")} for p in orphans
    ]
    state["definition"] = ("orphan pages: published pages not linked from any WebsiteMenu, "
                           "so unreachable from navigation and effectively unread")
    state["caveat"] = ("the platform records no pageview/traffic data (conversion_attribution "
                       "reads 0 site-wide), so this uses reachability as a proxy, not real reads")


def run_refusal(client, state):
    """Impossible ask: 'exact view count for every page.' Correct answer is a refusal,
    because the platform stores no readership data. It must not invent numbers."""
    state["refused"] = True
    state["refuse_reason"] = ("AgentSwitch stores no per-page view/visitor counts, so exact "
                              "readership numbers cannot be produced. I can instead return "
                              "orphan / zero-conversion pages and say so honestly.")
