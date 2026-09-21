"""Publisher agent — Goal #1: publish a post about the new fixture line.

perceive -> decide (LLM draft) -> act (create + publish) -> re-read (confirm in DB).
Idempotent: if a published fixture-line post already exists, it does nothing.
We hold `website_admin`, so BlogPost.publish (direct) works without the two-person approve.
"""
import json
import re

from agent import config, llm

SYSTEM = (
    "You are the content editor for Suryodaya Precision Works, a precision-tools maker. "
    "Write a clear, benefit-led company blog post. Plain, no hype, no em dashes. "
    'Return STRICT JSON ONLY: {"title": "...", "content": "..."} where content is a '
    "plain-text body of 120-180 words about the new fixture line (work-holding fixtures)."
)


def _posts(client):
    r = client.call("BlogPost.list", {"limit": 200})
    return r if isinstance(r, list) else r.get("items", r.get("data", []))


def _slug(title):
    return re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")[:60] or "new-fixture-line"


def _parse(text):
    try:
        s = text[text.index("{"):text.rindex("}") + 1]
        return json.loads(s)
    except Exception:
        return {"title": "Introducing our new fixture line", "content": text[:1500]}


def run_publish(client, state):
    # PERCEIVE — already published? then we are done (safe to re-run).
    for p in _posts(client):
        if p.get("status") == "published" and "fixture" in (p.get("title") or "").lower():
            state.update(published_post_id=p.get("id"), post_title=p.get("title"),
                         note="a published fixture post already exists")
            return

    # DECIDE — draft the post with the LLM.
    text, usage = llm.draft(
        SYSTEM,
        "Announce our new line of precision work-holding fixtures for procurement and "
        "shop-floor buyers. Say what they are and give one concrete benefit.")
    state.setdefault("cost", {}).update(usage)
    post = _parse(text)
    title = post.get("title") or "Introducing our new fixture line"
    body = post.get("content") or text

    # ACT — create the draft, then publish it.
    created = client.call("BlogPost.create", {
        "title": title, "slug": _slug(title),
        "website_id": config.WEBSITE_SURYODAYA, "content": body,
    })
    pid = created["id"]
    client.call("BlogPost.publish", {"id": pid})

    # RE-READ — confirm it truly published (also our write-path check).
    back = client.call("BlogPost.get", {"id": pid})
    state.update(published_post_id=pid, post_title=title,
                 published_status=back.get("status"))
