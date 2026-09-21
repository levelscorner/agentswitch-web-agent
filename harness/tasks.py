"""The task set. Each task = id, description, an optional agent runner, a verifier.

Runners are wired in as the agent is built. Read-only tasks have run=None and pass
immediately once we are logged in, which proves the harness runs end to end today.
"""
from . import verifiers as V
from agent.publisher import run_publish
from agent.analyst import run_analyst, run_refusal


TASKS = [
    {
        "id": "seat_access",
        "desc": "our seat can use the website app",
        "run": None,
        "verify": lambda c, s: V.seat_has_website_access(c),
    },
    {
        "id": "site_has_published_pages",
        "desc": "the site has at least 1 published page",
        "run": None,
        "verify": lambda c, s: V.site_has_published_pages(c, minimum=1),
    },
    {
        "id": "publish_fixture_post",
        "desc": "a published fixture-line post exists (Goal #1)",
        "run": run_publish,
        "verify": lambda c, s: V.published_fixture_post_exists(c),
    },
    {
        "id": "dead_pages_match",
        "desc": "the agent's dead-pages list matches the DB (Goal #2)",
        "run": run_analyst,
        "verify": lambda c, s: V.dead_pages_answer_matches(c, s),
    },
    {
        "id": "refusal_true_pageviews",
        "desc": "asked for real pageviews, the agent refuses instead of inventing",
        "run": run_refusal,
        "verify": lambda c, s: V.agent_refused(c, s),
    },
]
