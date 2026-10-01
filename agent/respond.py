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

from agent import config, llm, memory, reliability, verify
from agent.client import Client
from agent.state import State
from agent.supervisor import Supervisor
from agent.subgraphs import dead_pages_subgraph, publish_subgraph
from agent.analyst import run_refusal

# The supervisor's roster. publish and dead_pages are real sub-agents (subgraphs) — each gets
# only a scoped slice of state; refuse is a trusted one-shot function. The supervisor decides,
# per request, which of these to call — a capability is only invoked if the plan needs it.
ROSTER = {"publish": publish_subgraph, "dead_pages": dead_pages_subgraph, "refuse": run_refusal}

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
        goals = [g for g in data.get("goals", []) if g in ROSTER]
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


def respond(prompt, client=None):
    client = client or Client.login()
    llm.set_breaker(reliability.Breaker())   # fresh per-run budget cap + circuit breaker
    mem = memory.Memory(client).seed_defaults()
    goals = plan(prompt)
    state = State({"prompt": prompt, "goals": goals,
                   "website_id": config.WEBSITE_SURYODAYA,        # global channel for sub-agents
                   "recalled_definition": mem.get_fact("orphan_definition")})  # S07: read first
    ctx = SimpleNamespace(client=client, memory=mem)
    sup = Supervisor(ROSTER)                 # the 'daddy' routes goals to workers / sub-agents
    sup.run(ctx, state, goals)               # S08 parallel + scoped subgraphs + verify barrier
    _refine(sup, ctx, state)                 # S17: one refine pass if a goal failed reality
    _remember(mem, state)                    # S07: write what we learned
    return goals, compose(state), state


def _remember(mem, state):
    if state.get("definition"):
        mem.set_fact("orphan_definition", state["definition"])
    if "dead_pages" in state:
        mem.set_fact("orphan_count", len(state["dead_pages"]))
    if state.get("published_post_id"):
        mem.add_episode({"goal": "publish", "post_id": state["published_post_id"]})


def _refine(sup, ctx, state):
    """If the Verifier flagged a goal as not landed, re-run that worker once through the
    supervisor (scoping preserved), then re-check. One pass only — the breaker caps work."""
    v = state.get("verify", {})
    if v.get("ok", True):
        return
    for g, res in v.get("goals", {}).items():
        if not res.get("ok"):
            sup.run_one(ctx, state, g)
    state["verify"] = verify.reality_check(ctx.client, state)


def main():
    prompt = " ".join(sys.argv[1:]) or (
        "Publish a post about the new fixture line, and tell me which pages nobody reads."
    )
    goals, answer, _ = respond(prompt)
    print(f"PROMPT: {prompt}\nPLAN:   {goals}\n\n{answer}")


if __name__ == "__main__":
    main()
