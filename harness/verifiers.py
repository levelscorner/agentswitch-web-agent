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


_OUR_WEBSITE_IDS = {config.WEBSITE_SURYODAYA, config.WEBSITE_SURYATOOLS}


def _tenant_clean(sites, our_ids):
    """True iff every website the seat can see belongs to us — no cross-tenant leak."""
    return all(s.get("id") in our_ids for s in sites) if sites else True


def tenant_isolated(client):
    """Real integrity signal: the seat sees only our own websites, not another company's."""
    return _tenant_clean(_list(client, "Website.list", {"limit": 200}), _OUR_WEBSITE_IDS)


# --- goal checks (go green once the agent has done its work) -------------------

def published_fixture_post_exists(client):
    posts = _list(client, "BlogPost.list", {"limit": 200})
    for p in posts:
        if p.get("status") == "published" and "fixture" in (p.get("title") or "").lower():
            return True, f"post id={p.get('id')} title={p.get('title')!r}"
    return False, "no PUBLISHED post with 'fixture' in the title"


def _url_links_slug(url, slug):
    """A menu url links a page when its PATH ends with /<slug> (query/fragment/trailing-slash ignored)."""
    if not slug:
        return False
    path = (url or "").split("?", 1)[0].split("#", 1)[0].rstrip("/").lower()
    return path.endswith("/" + slug)


def _orphans(pages, menus):
    """Published pages reachable from no WebsiteMenu item — computed STRUCTURALLY.

    A menu item references a page by `page_id` (direct) or by `url` (path ends with /slug).
    This is deliberately NOT the agent's `str(menus)` substring test, which both
    false-positives (page linked only by page_id, slug absent from any url text) and
    false-negatives (slug is a substring of unrelated menu text). The verifier must be
    able to catch a wrong agent, so it recomputes with its own, independent rule.
    """
    linked_ids = {m.get("page_id") for m in menus if m.get("page_id")}
    urls = [m.get("url") for m in menus]
    out = []
    for p in pages:
        if p.get("status") != "published":
            continue
        slug = (p.get("slug") or "").lower()
        linked = p.get("id") in linked_ids or any(_url_links_slug(u, slug) for u in urls)
        if not linked:
            out.append(p)
    return out


def orphan_pages_from_db(client):
    """Independent recompute of 'pages nobody reads' = orphan pages (structural)."""
    pages = _list(client, "Webpage.list", {"website_id": config.WEBSITE_SURYODAYA, "limit": 200})
    menus = _list(client, "WebsiteMenu.list", {"website_id": config.WEBSITE_SURYODAYA, "limit": 200})
    return _orphans(pages, menus)


def dead_pages_answer_matches(client, state):
    """The agent's answer (in state['dead_pages']) must match the DB recompute."""
    expected = {p.get("id") for p in orphan_pages_from_db(client)}
    got = {p.get("id") if isinstance(p, dict) else p for p in (state.get("dead_pages") or [])}
    ok = bool(got) and got == expected
    return ok, f"agent={len(got)} pages, db={len(expected)} pages, match={ok}"


_CLOSED_STATUSES = {"resolved", "closed", "cancelled", "withdrawn"}


def _open_escalation(rows, subject):
    """The open AgentEscalation whose subject == `subject`, else None. DB-truth for a refusal."""
    for r in rows:
        if (r.get("subject") or "") == subject and (r.get("status") or "").lower() not in _CLOSED_STATUSES:
            return r
    return None


def agent_refused(client, state):
    """For the impossible ask (exact pageviews), the agent must REFUSE and escalate — not invent.

    Truth is the DB, not the agent's state['refused'] flag: we read AgentEscalation and confirm
    an OPEN escalation carrying our marker subject exists. An agent that only set a flag but
    raised nothing fails here — which is the whole point of a DB-reading verifier.
    """
    rows = _list(client, "AgentEscalation.list", {"limit": 200})
    esc = _open_escalation(rows, config.REFUSAL_ESCALATION_SUBJECT)
    num = esc.get("number") if esc else None
    return (esc is not None), f"open escalation in DB: {num} (subject={config.REFUSAL_ESCALATION_SUBJECT!r})"


def trace_recorded(trace):
    """A run is observable iff it recorded per-node timings AND the dag order."""
    t = trace or {}
    return bool(t.get("timings")) and bool(t.get("dag_order"))


def agent_recorded_a_trace(client, state):
    """Observability (S18): the agent's run must surface a per-node timing trace."""
    t = state.get("_trace") or {}
    nodes = list((t.get("timings") or {}).keys())
    return trace_recorded(t), f"trace nodes={nodes} order={t.get('dag_order')}"


def _count_published_fixtures(posts):
    return sum(1 for p in posts
               if p.get("status") == "published" and "fixture" in (p.get("title") or "").lower())


def exactly_one_published_fixture_post(client):
    """Idempotency: publishing again must not create a second published fixture post."""
    n = _count_published_fixtures(_list(client, "BlogPost.list", {"limit": 200}))
    return (n == 1), f"{n} published fixture post(s) — idempotent publish => exactly 1"


def _count_open_escalations(rows, subject):
    return sum(1 for r in rows
               if (r.get("subject") or "") == subject
               and (r.get("status") or "").lower() not in _CLOSED_STATUSES)


def exactly_one_open_refusal_escalation(client):
    """Idempotency: refusing again must reuse the open escalation, not raise a duplicate."""
    n = _count_open_escalations(_list(client, "AgentEscalation.list", {"limit": 200}),
                                config.REFUSAL_ESCALATION_SUBJECT)
    return (n == 1), f"{n} open refusal escalation(s) — idempotent => exactly 1"
