"""Natural-language entrypoint: take the graded request as one sentence, plan it into
goals, run them, and speak a combined answer.

    set -a; source .env; set +a
    python3 -m agent.respond "Publish a post about the new fixture line, and tell me which pages nobody reads."

This is the S05 planner on top of the S06 loops: an LLM maps the request to a small set of
goals, then we execute each goal deterministically and compose a human-facing reply from the
DB-verified state. Grading reads DB state, not this text; the text is for the human/demo.
"""
import json
import sys

from agent import llm
from agent.client import Client
from agent.publisher import run_publish
from agent.analyst import run_analyst, run_refusal

GOALS = {"publish": run_publish, "dead_pages": run_analyst, "refuse": run_refusal}

PLANNER_SYSTEM = (
    "You route a website-agent request to goals. Available goals:\n"
    "  publish     - publish a blog post (asked to publish / write / post something)\n"
    "  dead_pages  - list pages nobody reads / pages with no traffic\n"
    "  refuse      - the user demands EXACT per-page view/visitor counts, which the platform "
    "does not store; the honest response is to refuse and explain\n"
    'Return STRICT JSON only: {"goals": [ ... ]} in the order they should run. '
    "Pick 'refuse' only for exact-view-count demands, not for the 'pages nobody reads' ask."
)


def plan(prompt):
    """LLM decides which goals the request needs; keyword routing is the fallback."""
    try:
        text, _ = llm.draft(PLANNER_SYSTEM, prompt, max_tokens=200)
        goals = json.loads(text[text.index("{"):text.rindex("}") + 1]).get("goals", [])
        goals = [g for g in goals if g in GOALS]
        if goals:
            return goals
    except Exception:
        pass
    return _keyword_plan(prompt)


def _keyword_plan(prompt):
    p = prompt.lower()
    goals = []
    if any(w in p for w in ("publish", "post", "write", "announce")):
        goals.append("publish")
    if any(w in p for w in ("exact view", "how many view", "view count", "pageview", "visitor count")):
        goals.append("refuse")
    elif any(w in p for w in ("nobody reads", "no traffic", "without traffic", "which pages", "unread")):
        goals.append("dead_pages")
    return goals or ["dead_pages"]


def compose(state):
    """A human-facing answer built only from DB-verified state."""
    parts = []
    if state.get("published_post_id"):
        parts.append(
            f"Published the post \"{state.get('post_title')}\" "
            f"(status: {state.get('published_status', 'published')})."
        )
    if "dead_pages" in state:
        pages = state["dead_pages"]
        listing = "\n".join(f"  - {p.get('title')} ({p.get('slug')})" for p in pages) or "  (none)"
        parts.append(
            f"Pages nobody reads ({len(pages)}):\n{listing}\n"
            f"Definition: {state.get('definition')}\n"
            f"Caveat: {state.get('caveat')}"
        )
    if state.get("refused"):
        parts.append(f"I can't produce exact pageview numbers. {state.get('refuse_reason')}")
    return "\n\n".join(parts) or "I could not map that request to anything I can do."


def respond(prompt, client=None):
    client = client or Client.login()
    goals = plan(prompt)
    state = {"prompt": prompt, "goals": goals}
    for g in goals:
        GOALS[g](client, state)
    return goals, compose(state), state


def main():
    prompt = " ".join(sys.argv[1:]) or (
        "Publish a post about the new fixture line, and tell me which pages nobody reads."
    )
    goals, answer, _ = respond(prompt)
    print(f"PROMPT: {prompt}\nPLAN:   {goals}\n\n{answer}")


if __name__ == "__main__":
    main()
