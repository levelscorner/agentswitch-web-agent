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


def _menu_links_slug(url, slug):
    """A menu url links a page when its PATH ends with /<slug> (query/fragment/slash ignored)."""
    if not slug:
        return False
    path = (url or "").split("?", 1)[0].split("#", 1)[0].rstrip("/").lower()
    return path.endswith("/" + slug)


_CONV_TOOL = "endpoint.website.conversion_attribution"


def _outcome_summary(result):
    """Reduce the conversion_attribution `result` to coverage + real attributed outcomes.
    Shape: {paths:[...per page-section...], summary:{conversions_attributed, attributed, ...}}."""
    result = result or {}
    paths = result.get("paths") or []
    summary = result.get("summary") or {}
    covered = len(paths)
    with_outcomes = int(summary.get("conversions_attributed")
                        or summary.get("attributed") or 0)
    return {"covered": covered, "with_outcomes": with_outcomes}


def _caveat_from(summary):
    """Honest caveat built from what conversion_attribution ACTUALLY returned, not an
    asserted 'reads 0'. If the probe was unavailable, the structural-proxy wording stands."""
    if not summary:
        return CAVEAT
    cov, wo = summary["covered"], summary["with_outcomes"]
    if wo == 0:
        return (f"checked conversion_attribution — 0 attributed conversions across {cov} "
                "attribution path(s), so the platform holds no real readership signal; "
                "this list uses menu-reachability as the proxy")
    return (f"checked conversion_attribution — {wo} attributed conversion(s) across {cov} "
            "path(s); this list still uses menu-reachability (orphan) as the 'unread' proxy")


def _probe_outcomes(ctx, s):
    """Actually ask the platform for outcomes instead of asserting 'reads 0'. Best-effort:
    any failure leaves _outcomes=None and the structural-proxy caveat stands."""
    try:
        r = ctx.client.call(_CONV_TOOL, {"website_id": s["website_id"]})
        result = (r or {}).get("result", r) if isinstance(r, dict) else None
        s["_outcomes"] = _outcome_summary(result) if result else None
    except Exception:
        s["_outcomes"] = None


def _detect_orphans(ctx, s):
    # Structural reachability: a page is linked when a menu item targets it by page_id
    # or a menu url path ends with its slug. (The old str(menus) substring test both
    # missed real orphans and invented fake ones.)
    menus = s.get("_menus") or []
    linked_ids = {m.get("page_id") for m in menus if m.get("page_id")}
    urls = [m.get("url") for m in menus]
    published = [p for p in (s.get("_pages") or []) if p.get("status") == "published"]
    orphans = [p for p in published
               if p.get("id") not in linked_ids
               and not any(_menu_links_slug(u, (p.get("slug") or "").lower()) for u in urls)]
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
    s["caveat"] = _caveat_from(s.get("_outcomes"))     # evidence-based, not asserted
    s["outcome_evidence"] = s.get("_outcomes")


def _build_dead_pages():
    return (DAG(max_workers=3)
            .add(Node("fetch_pages", _fetch_pages))
            .add(Node("fetch_menus", _fetch_menus))
            .add(Node("probe_outcomes", _probe_outcomes))
            .add(Node("detect", _detect_orphans, deps=["fetch_pages", "fetch_menus"]))
            .add(Node("assemble", _assemble, deps=["detect", "probe_outcomes"])))


dead_pages_subgraph = Subgraph(
    name="dead_pages",
    inputs=["website_id"],
    outputs=["dead_pages", "definition", "caveat", "outcome_evidence"],
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


_CAP_TOOL = "endpoint.website.editor_capabilities"


def _editor_can_create(client, website_id):
    """Best-effort read of our publish/create grant. Informational only — never blocks,
    returns None if the capability endpoint is unavailable."""
    try:
        r = client.call(_CAP_TOOL, {"website_id": website_id})
        return bool(r.get("can_create_page")) if isinstance(r, dict) else None
    except Exception:
        return None


def _publish_with_fallback(client, pid):
    """Direct publish (we hold website_admin); if that is unavailable — e.g. a grant change
    like R8.1 pulling a tool — fall back to the review workflow, and if even that is blocked,
    leave a clean draft rather than crash. Returns an honest note; never raises."""
    try:
        client.call("BlogPost.publish", {"id": pid})
        return "published directly (website_admin)"
    except Exception:
        pass
    try:
        client.call("BlogPost.submit_for_review", {"id": pid})
        return "submitted for review (direct publish unavailable; needs a second-seat approval)"
    except Exception:
        return "left as draft (publish and review paths both unavailable)"


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
        s["editor_can_create"] = _editor_can_create(ctx.client, s["website_id"])
        created = ctx.client.call("BlogPost.create", {
            "title": s["_title"], "slug": _pub_slug(s["_title"]),
            "website_id": s["website_id"], "content": s["_body"]})
        pid, title = created["id"], s["_title"]
    # Fallback chain instead of publish-or-crash: a blocked write leaves a reusable draft
    # (idempotent on the next run) rather than raising. _pub_reread records the real status.
    s["publish_note"] = _publish_with_fallback(ctx.client, pid)
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
