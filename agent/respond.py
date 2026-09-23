"""Natural-language entrypoint: take the graded request as one sentence, plan it into
goals, run them, and speak a combined answer.

    set -a; source .env; set +a
    python3 -m agent.respond "Publish a post about the new fixture line, and tell me which pages nobody reads."

This is the S05 planner on top of the S06 loops: an LLM maps the request to a small set of
goals, then we execute each goal deterministically and compose a human-facing reply from the
DB-verified state. Grading reads DB state, not this text; the text is for the human/demo.
"""
import sys
from types import SimpleNamespace

from agent import llm, reliability, verify
from agent.client import Client
from agent.dag import DAG, Node
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
        data = llm.draft_json(PLANNER_SYSTEM, prompt, tier="simple", max_tokens=200)
        goals = [g for g in data.get("goals", []) if g in GOALS]
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
    v = state.get("verify")
    if v and v.get("goals"):
        line = "; ".join(f"{g} {'OK' if r['ok'] else 'FAILED (' + r['note'] + ')'}"
                         for g, r in v["goals"].items())
        parts.append("Verified against the DB: " + line)
    return "\n\n".join(parts) or "I could not map that request to anything I can do."


def build_dag(goals):
    """Wire the planned goals into a DAG (S08). publish and dead_pages are
    independent, so the engine runs them in parallel; refuse stands alone.
    Each node adapts a goal function (client, state) into a node run (ctx, state)."""
    dag = DAG(max_workers=3)
    for g in goals:
        fn = GOALS[g]
        dag.add(Node(g, lambda ctx, s, fn=fn: fn(ctx.client, s)))
    dag.add(Node("verify", lambda ctx, s: verify.run_verify(ctx.client, s), deps=list(goals)))
    return dag


def respond(prompt, client=None):
    client = client or Client.login()
    llm.set_breaker(reliability.Breaker())   # fresh per-run budget cap + circuit breaker
    goals = plan(prompt)
    state = {"prompt": prompt, "goals": goals}
    ctx = SimpleNamespace(client=client)
    build_dag(goals).run(ctx, state)
    _refine(ctx, state)                      # S17: one refine pass if a goal failed reality
    return goals, compose(state), state


def _refine(ctx, state):
    """If the Verifier flagged a goal as not landed, re-run that goal once, then
    re-check. One pass only — the breaker still caps total work."""
    v = state.get("verify", {})
    if v.get("ok", True):
        return
    for g, res in v.get("goals", {}).items():
        if not res.get("ok") and g in GOALS:
            GOALS[g](ctx.client, state)
    state["verify"] = verify.reality_check(ctx.client, state)


def main():
    prompt = " ".join(sys.argv[1:]) or (
        "Publish a post about the new fixture line, and tell me which pages nobody reads."
    )
    goals, answer, _ = respond(prompt)
    print(f"PROMPT: {prompt}\nPLAN:   {goals}\n\n{answer}")


if __name__ == "__main__":
    main()
