# Plan — four weeks, week by week

Fixed four-week schedule (it does not extend). Weekly commits land on the repo the instructor
reviews. Grading is on the gap report, the agent, the harness, hand-written tests, and bugs found.

---

## Where we are right now

- [x] Signed in; confirmed seat (`team09`, Website, apps `website/agent/crm`).
- [x] Called the live API end to end over MCP (Bearer path) — 236 tools mapped.
- [x] Isolated our 36 website tools; found the `Webpage`/`BlogPost` publish workflows.
- [x] Found the two goal IDs: `web.publish_post`, `web.pages_without_traffic`.
- [x] Discovered the key gap: **no raw page-view data**, only `conversion_attribution`.
- [x] Repo, `probe.py`, Bruno collection, capability notes.
- [x] **Gap report written** — `docs/gap-report.md` (the missing pageview primitive vs Ghost / Plausible / Fathom).
- [x] Scraped the live site (51 pages, 100 posts; conversions all zero) — `research/domain-understanding-2026-09-17.md`.
- [ ] Last Week-1 item: **file one real bug** (candidate identified, see Week 1 below).

---

## Week 1 — learn the domain, find the product, write the gap report

**Goal:** understand our seat deeply and produce the one graded Week-1 deliverable.

- [x] Log in, read the seat in the UI, call the API.
- [x] **Gap report** (the deliverable) — done: [`gap-report.md`](gap-report.md). Three questions
  answered against Ghost (publishing + native analytics) and Plausible / Fathom (traffic API),
  grounded in our live scrape. Core finding: the gap is one missing data primitive (a pageview
  table), not the protocol.
- [ ] **File one real, reproducible bug** not on the class board (100 pts; known bugs = 0).
  Two candidates investigated 2026-09-17 and **refuted** (`page_type` = seed noise on a closed
  enum; the role "discrepancy" = an intended shared-DB mutation), and a read-only invariant sweep
  came back clean — see [`../research/bug-hunt-log.md`](../research/bug-hunt-log.md). Real bug
  territory is **write-path silent no-ops**, to test with before/after DB reads during the build.

**Done when:** `docs/gap-report.md` exists (done) and one bug is filed.

---

## Week 2 — first agent answers one goal, judged by its predicate

**Goal:** a working agent that makes one goal pass from database state.

- [ ] `agent/mcp_client.py` — `login()` + `call(name, args)` on the Bearer path.
- [ ] Implement the smaller half first: **`web.publish_post`** — create a draft about the
  fixture line and drive it to published (pin down publish-vs-review for our editor role).
- [ ] A first harness task + verifier that reads the DB ("a published fixture post exists").
- [ ] Commit to the reviewed repo/branch.

**Done when:** running the agent makes `web.publish_post` verifiably pass, and the run is
journaled to disk before scoring.

---

## Week 3 — the second goal, the harness, and breadth

**Goal:** both goals solid, and the harness that most teams underbuild.

- [ ] **`web.pages_without_traffic`** — define "no traffic" from `conversion_attribution`,
  compute the zero-engagement pages, and verify the set against the DB.
- [ ] **Refusal task** — a request the data cannot support (e.g. true readership, which is not
  tracked); the agent must say so instead of inventing a number.
- [ ] Grow the harness: many **hand-written** tests (10 pts each), each verifying from the DB.
- [ ] **Breadth:** run the agent against the other verticals (school / clinic / retail / agency)
  and the **Keystone (US)** business — no hardcoded manufacturing nouns. Finding a hardcode in
  Week 4 means a rewrite, so exercise breadth now.

**Done when:** both predicates pass, a refusal task passes, and the harness runs a real test set.

---

## Week 4 — harden, test, hunt bugs, finalize

**Goal:** maximise verifiable points and lock it in.

- [ ] Harden: retries, re-reading changed state, tolerating other teams' writes.
- [ ] Expand hand-written tests toward the high end (points scale with count).
- [ ] Hunt **new reproducible bugs** (100 pts each) — check the board first.
- [ ] Tidy the repo, refresh the README/diagrams, confirm everything runs top to bottom.
- [ ] Phase-A "done" teams are considered for **Phase B** (the 8 advanced agents).

**Done when:** the deadline; the repo runs clean, tests pass, points are banked.

---

## Standing rules (apply every week)

- Grading reads **DB state after the run**, not the reply text.
- Verifiers read the **database**, not the agent's prose; journal every run **before** scoring.
- **Never** write outside our seat or edit shared data to force our own goal to pass — every
  write is attributed.
- Commit weekly to the reviewed repo; the instructor checks progress there.
- If our seat genuinely cannot be done without changing the harness/predicates/schemas, that is
  a **bug report with a reproducing case**, not a local fork.
