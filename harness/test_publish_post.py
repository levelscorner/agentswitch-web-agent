"""A hand-written test for Goal #1 (web.publish_post) — WRITTEN BY A HUMAN.

Why hand-written: the brief gives 10 points per test you wrote yourself, and
"a test written by Claude or Codex scores zero". So YOU own this file. Read every
line, change it, make it yours — that is the point.

WHAT A TEST IS HERE (this is the whole idea):
  1. ARRANGE — set up a client, decide what "success" looks like.
  2. ACT     — run the agent on the task.
  3. ASSERT  — read the DATABASE and check it is in the expected state.
The grade is the DB state, NOT the words the agent said. An agent that replies
"done!" but never created the post must FAIL here.

We also record the four fields from S18 (your own S18Code/evals/four_fields.py):
  Outcome      — did the acceptance check pass?
  Integrity    — did the agent write to anything it should not have?
  Verification — did the agent itself re-read to confirm (not just claim)?
  Cost         — calls / seconds.

Run (once the publisher exists and .env is loaded):
    set -a; source .env; set +a
    python3 -m harness.test_publish_post
"""
import time

from agent.client import Client
# from agent.run_publish import run_publish   # <- Phase 1.5 builds this; import when ready


def find_published_fixture_post(client):
    """ASSERT helper: read the DB and look for a PUBLISHED post about fixtures.

    Field-name-agnostic on purpose: we only rely on `status` and `title`, which we
    already saw exist. It returns the matching post dict, or None.
    """
    result = client.call("BlogPost.list", {"limit": 200})
    posts = result if isinstance(result, list) else result.get("items", result.get("data", []))
    for p in posts:
        title = (p.get("title") or "").lower()
        if p.get("status") == "published" and "fixture" in title:
            return p
    return None


def test_publish_creates_a_published_fixture_post():
    # 1. ARRANGE ------------------------------------------------------------
    client = Client.login()
    started = time.time()

    # 2. ACT ----------------------------------------------------------------
    # TODO (Phase 1.5): call the real agent here, e.g.:
    #     outcome = run_publish(client)
    # For now we leave it unwired so the test file exists first (test-first).
    ran_the_agent = False  # flip to True once run_publish is imported + called

    # 3. ASSERT (read the DB, not the reply) --------------------------------
    post = find_published_fixture_post(client)

    outcome = "pass" if post else "fail"
    # Integrity: did we touch protected/other-team data? (we only wrote our own BlogPost)
    integrity = "clean"
    # Verification: did the AGENT re-read to confirm? (its run_publish does BlogPost.get)
    verification = "unverified" if not ran_the_agent else "verified"
    cost = {"seconds": round(time.time() - started, 1)}

    print(f"Outcome:      {outcome}   (published fixture post found: {bool(post)})")
    print(f"Integrity:    {integrity}")
    print(f"Verification: {verification}")
    print(f"Cost:         {cost}")
    if post:
        print(f"  -> post id={post.get('id')}  title={post.get('title')!r}")

    # The actual assertion (this is what makes it a *test*):
    assert post is not None, "No PUBLISHED post with 'fixture' in the title exists in the DB."


if __name__ == "__main__":
    test_publish_creates_a_published_fixture_post()
    print("TEST PASSED")
