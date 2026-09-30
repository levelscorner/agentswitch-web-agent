"""Concrete sub-agents (subgraphs) for the Website seat.

`dead_pages` is now a REAL sub-agent, not a flat function: it gets a scoped input
(only `website_id`), runs its own internal DAG — fetch pages ‖ fetch menus → detect
→ assemble — appends findings into a reducer channel, and returns only its three
output channels. Its scratch (`_pages`, `_menus`) stays private to the subgraph.
"""
from agent import config
from agent.dag import DAG, Node
from agent.subgraph import Subgraph

DEFINITION = ("orphan pages: published pages not linked from any WebsiteMenu, "
              "so unreachable from navigation and effectively unread")
CAVEAT = ("the platform records no pageview/traffic data (conversion_attribution "
          "reads 0 site-wide), so this uses reachability as a proxy, not real reads")


def _list(client, name, args):
    r = client.call(name, args)
    return r if isinstance(r, list) else r.get("items", r.get("data", r.get("results", [])))


def _fetch_pages(ctx, s):
    s["_pages"] = _list(ctx.client, "Webpage.list", {"website_id": s["website_id"], "limit": 200})


def _fetch_menus(ctx, s):
    s["_menus"] = _list(ctx.client, "WebsiteMenu.list", {"website_id": s["website_id"], "limit": 200})


def _detect_orphans(ctx, s):
    published = [p for p in (s.get("_pages") or []) if p.get("status") == "published"]
    blob = str(s.get("_menus") or []).lower()
    orphans = [p for p in published if (p.get("slug") or "").lower() not in blob]
    s.merge("dead_pages_candidates",
            [{"id": p.get("id"), "title": p.get("title"), "slug": p.get("slug")} for p in orphans])


def _assemble(ctx, s):
    seen, out = set(), []
    for p in s.get("dead_pages_candidates") or []:
        if p["id"] not in seen:
            seen.add(p["id"])
            out.append(p)
    s["dead_pages"] = out
    s["definition"] = DEFINITION
    s["caveat"] = CAVEAT


def _build_dead_pages():
    return (DAG(max_workers=2)
            .add(Node("fetch_pages", _fetch_pages))
            .add(Node("fetch_menus", _fetch_menus))
            .add(Node("detect", _detect_orphans, deps=["fetch_pages", "fetch_menus"]))
            .add(Node("assemble", _assemble, deps=["detect"])))


dead_pages_subgraph = Subgraph(
    name="dead_pages",
    inputs=["website_id"],
    outputs=["dead_pages", "definition", "caveat"],
    build=_build_dead_pages,
)
