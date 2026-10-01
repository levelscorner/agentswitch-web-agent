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
    """Goal #1 now runs as a real sub-agent (perceive -> decide -> act -> re-read with
    idempotency + compensation). This is the compatibility entry point (the harness and
    any legacy caller use it): hand the publish subgraph a scoped input, copy outputs back.
    The helpers above (SYSTEM, _parse, _slug) are imported by that subgraph."""
    from agent.subgraphs import publish_subgraph   # local import avoids an import cycle
    out = publish_subgraph.run(client, {"website_id": config.WEBSITE_SURYODAYA})
    state.update(out)
