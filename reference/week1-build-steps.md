# Week-1 build — atomic steps

Small, verifiable steps. Each has an owner: **[me]** I write it · **[you]** you run/own it ·
**[pair]** we do together. Gap report + domain scrape are already done, so this front-loads the
first agent goal.

## Phase 0 — foundation (client that talks to the platform)

- [x] **0.1 [me]** `agent/` package + `agent/config.py` (reads `.env`, holds the website IDs).
- [x] **0.2 [me]** `agent/client.py` — `Client.login()` → Bearer token; `.call(name, args)`;
  raises on the HTTP-200 JSON-RPC error. Never prints the token.
- [ ] **0.3 [you]** put your Suryodaya password in `.env` (`AS_PASSWORD=`) and one model key.
- [ ] **0.4 [you]** run it — **verify:** prints `team09`, our roles, and `MCP tools visible: 236`.
  ```bash
  cd agent-repo && set -a; source .env; set +a
  python3 -m agent.client
  ```

## Phase 1 — Goal #1: publish the fixture-line post (the tangible win)

- [ ] **1.1 [me]** `agent/perception.py::find_fixture_post()` — `BlogPost.list`, search for an
  existing fixture-line post so we don't double-publish.
- [ ] **1.2 [pair]** `agent/draft.py::draft_post(topic)` — **you own the prompt + house style**
  (you know the tone); I wire the model call. Output: title + body + category.
- [ ] **1.3 [me]** `agent/publish.py::create_and_publish(post)` — `BlogPost.create` (draft) →
  `BlogPost.publish` (we hold `website_admin`, so likely direct).
- [ ] **1.4 [me]** `agent/verify.py::assert_published(title)` — `BlogPost.get`, assert
  `status == published`. **Reads the DB, not the agent's words.**
- [ ] **1.5 [me]** `agent/run_publish.py` — wire perceive → draft → create → publish → verify.
- [ ] **1.6 [you / approve]** **LIVE proof run.** Publishes the post; the verifier confirms the
  DB flipped. This is also our **write-path bug test** (does publish silently no-op?).

## Phase 2 — first harness task (the S18 shape)

- [ ] **2.1 [me]** `harness/verifiers.py::published_fixture_post_exists()` — DB read → bool + evidence.
- [ ] **2.2 [me]** `harness/run.py` — run the task, **write the raw run journal to disk BEFORE
  scoring**, then four-field score (Outcome / Integrity / Verification / Cost).
- [ ] **2.3 [you]** run the harness → see `pass` and the journal file. **Week-1 milestone reached.**

## Phase 3 — Goal #2 + the refusal (starts now, finishes into Week 2)

- [ ] **3.1 [me]** `agent/pages.py::load()` — `Webpage.list` (published) + `WebsiteMenu.list` + page links.
- [ ] **3.2 [pair]** `agent/orphans.py::compute()` — define "no traffic" = **orphan pages**
  (published, not in any menu, not linked from another page).
- [ ] **3.3 [me]** answer + honest caveat (conversions are all zero; true readership isn't tracked);
  verifier recomputes orphans independently and compares.
- [ ] **3.4 [me]** refusal task — asked for true pageviews, the agent declines; verifier checks it
  refused instead of inventing.

**Definition of done for Week 1:** Phase 0 + 1 + 2 green — a working agent that publishes the
fixture post and a harness that proves it from the database, plus one bug filed if the write-path
test surfaces one.
