"""Official AgentSwitch run entry point (Release 8.1): `python -m harness.runner`.

Everything comes from environment variables the course runner sets — no login, no
.env, no keys of our own:
  AGENTSWITCH_BASE_URL   the (fresh, throwaway) instance to call
  AGENTSWITCH_TOKEN      our seat's bearer token
  AGENTSWITCH_INSTANCE   suryodaya | keystone  (labels the task ids)
  OPENAI_BASE_URL/KEY/MODEL   the platform model (picked up by agent/llm.py)

It reuses our real task set + DB-truth verifiers (harness/tasks.py, run_one) and
writes results.json in the grader's schema. Local rehearsal:

  set -a; source .env; set +a
  TOK=$(python -c "from agent.client import Client; print(Client.login()._token)")
  AGENTSWITCH_BASE_URL=https://agentswitch.theschoolofai.in \
  AGENTSWITCH_TOKEN=$TOK AGENTSWITCH_INSTANCE=suryodaya python -m harness.runner
"""
import json
import os

from agent.client import Client
from agent import config
from harness import verifiers as V
from harness.run import run_one
from harness.tasks import TASKS


def _resolve_websites(client):
    """A fresh instance copy may not keep our hard-coded website ids, so discover them
    from Website.list and point config at the real ones before any task runs."""
    r = client.call("Website.list", {"limit": 200})
    sites = r if isinstance(r, list) else r.get("items", r.get("data", r.get("results", [])))
    ids = [s.get("id") for s in sites if s.get("id")]
    if not ids:
        return
    # prefer the 'suryodaya'-looking site as primary, else just the first
    def looks_suryodaya(s):
        return "suryodaya" in (s.get("name") or s.get("_display") or "").lower()
    primary = next((s.get("id") for s in sites if looks_suryodaya(s)), ids[0])
    config.WEBSITE_SURYODAYA = primary
    others = [i for i in ids if i != primary]
    if others:
        config.WEBSITE_SURYATOOLS = others[0]
    V._OUR_WEBSITE_IDS = set(ids)   # integrity check: every visible site is ours


def main():
    base = os.environ["AGENTSWITCH_BASE_URL"].rstrip("/")
    client = Client(base, os.environ["AGENTSWITCH_TOKEN"])   # token, not login
    instance = os.environ.get("AGENTSWITCH_INSTANCE", "suryodaya")

    try:
        _resolve_websites(client)
    except Exception as exc:  # noqa: BLE001 — never let discovery abort the whole run
        print(f"[warn] website resolve failed ({exc!r}); using configured ids", flush=True)

    out = []
    for task in TASKS:
        score = run_one(client, task)          # runs the agent + DB-truth verify
        passed = score.outcome == "pass"
        out.append({
            "id": f"{instance}:{task['id']}",
            "title": task["desc"],
            "passed": bool(passed),
            "score": 1.0 if passed else 0.0,
            "evidence": str(score.evidence)[:500],
        })
        print(f"[{'PASS' if passed else 'FAIL'}] {task['id']}: {str(score.evidence)[:160]}", flush=True)

    npass = sum(1 for t in out if t["passed"])
    with open("results.json", "w") as fh:
        json.dump({"tasks": out,
                   "summary": f"{instance}: {npass}/{len(out)} tasks passed"}, fh, indent=2)
    print(f"\n{npass}/{len(out)} passed -> results.json", flush=True)


if __name__ == "__main__":
    main()
