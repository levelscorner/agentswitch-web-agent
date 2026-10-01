"""Concrete sub-agents (subgraphs) for the Website seat.

`dead_pages` is now a REAL sub-agent, not a flat function: it gets a scoped input
(only `website_id`), runs its own internal DAG — fetch pages ‖ fetch menus → detect
→ assemble — appends findings into a reducer channel, and returns only its three
output channels. Its scratch (`_pages`, `_menus`) stays private to the subgraph.
"""
from agent import config, llm
from agent.dag import DAG, Node
from agent.subgraph import Subgraph
from agent.publisher import SYSTEM as PUB_SYSTEM, _parse as _pub_parse, _slug as _pub_slug

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


# --- publish sub-agent: perceive -> decide -> act -> re-read, with idempotency + compensation ---

def _fixture(posts, *statuses):
    for p in posts:
        if p.get("status") in statuses and "fixture" in (p.get("title") or "").lower():
            return p
    return None


def _pub_perceive(ctx, s):
    posts = _list(ctx.client, "BlogPost.list", {"limit": 200})
    s["_published"] = _fixture(posts, "published")              # idempotency: already done?
    s["_draft"] = _fixture(posts, None, "draft")               # idempotency+: a half-done draft to reuse


def _pub_decide(ctx, s):
    if s.get("_published") or s.get("_draft"):
        return                                                 # reuse — no need to draft
    text, _ = llm.draft(PUB_SYSTEM,
                        "Announce our new line of precision work-holding fixtures for procurement and "
                        "shop-floor buyers. Say what they are and give one concrete benefit.")
    post = _pub_parse(text)
    s["_title"] = post.get("title") or "Introducing our new fixture line"
    s["_body"] = post.get("content") or text


def _pub_act(ctx, s):
    if s.get("_published"):                                     # already published: reuse, write nothing
        p = s["_published"]
        s.update(published_post_id=p.get("id"), post_title=p.get("title"),
                 published_status="published", note="already published (idempotent)")
        return
    if s.get("_draft"):                                        # reuse a half-done draft (crash-safe)
        pid, title = s["_draft"].get("id"), s["_draft"].get("title")
        s["note"] = "reused an existing draft (idempotent)"
    else:
        created = ctx.client.call("BlogPost.create", {
            "title": s["_title"], "slug": _pub_slug(s["_title"]),
            "website_id": s["website_id"], "content": s["_body"]})
        pid, title = created["id"], s["_title"]
    try:
        ctx.client.call("BlogPost.publish", {"id": pid})
    except Exception:
        try:
            ctx.client.call("BlogPost.archive", {"id": pid})   # compensation: undo the orphaned create
        except Exception:
            pass
        raise
    s.update(_pid=pid, post_title=title)


def _pub_reread(ctx, s):
    pid = s.get("_pid") or s.get("published_post_id")
    if not pid:
        return
    back = ctx.client.call("BlogPost.get", {"id": pid})
    s.update(published_post_id=pid, published_status=back.get("status"))


def _build_publish():
    return (DAG(max_workers=1)
            .add(Node("perceive", _pub_perceive))
            .add(Node("decide", _pub_decide, deps=["perceive"]))
            .add(Node("act", _pub_act, deps=["decide"]))
            .add(Node("reread", _pub_reread, deps=["act"])))


publish_subgraph = Subgraph(
    name="publish",
    inputs=["website_id"],
    outputs=["published_post_id", "post_title", "published_status", "note"],
    build=_build_publish,
)
