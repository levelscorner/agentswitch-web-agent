# Harness — our own eval rig (S18)

Runs the agent on a task set and **scores it by reading the database**, never the reply.
Every run is journaled to disk **before** scoring, so scores are recomputable.

## Files

- `four_fields.py` — the score type: Outcome · Integrity · Verification · Cost.
- `verifiers.py` — DB-reading checks (each returns `(passed, evidence)`).
- `tasks.py` — the task set (read-only checks pass today; goal checks go green as the agent is built).
- `run.py` — the runner: run task → journal to disk → four-field score → print table.
- `test_publish_post.py` — a hand-written test for Goal #1 (you own this; hand-written = points).
- `bughunt.py` — write-path bug hunter (create/publish/cleanup, flags "success but no DB change").
- `adapter.py` — **integration seam** for an external harness: one prompt in → one graded JSON out.

## Run

```bash
set -a; source .env; set +a          # loads AS_PASSWORD etc.

python3 -m harness.run               # the scored task table (read-only tasks pass now)
python3 -m harness.bughunt           # dry: dump create-schemas + plan (no writes)
python3 -m harness.bughunt --run     # live: create/publish/cleanup + report bug candidates
python3 -m harness.test_publish_post # the single hand-written Goal-1 test
```

## External integration (Week-2 course harness)

`adapter.py` is the single seam the course harness plugs into — map their call to
`run()` here, nothing else changes.

```bash
# shell: JSON in → graded JSON out
echo '{"prompt":"Publish ... which pages nobody reads?"}' | python3 -m harness.adapter
```

```python
# import: reuse an authenticated client
from harness.adapter import run
result = run(prompt, client=my_client)   # {ok, plan, answer, verify, seconds}
```

`ok`/`verify` are computed by re-reading the DB (`agent/verify.py`) — that is the
truth to score. `answer` is human-facing text, never the ground truth.

## Scoring

| Field | Question |
|---|---|
| Outcome | did the acceptance check (DB truth) pass? |
| Integrity | did the agent write to anything it shouldn't? |
| Verification | did the agent itself re-read to confirm (not just claim)? |
| Cost | calls / seconds |
