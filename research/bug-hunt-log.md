# Bug-hunt log

Honest record of what we checked and why we did (not) file. A report that cannot be reproduced,
or that describes intended/seed behaviour, scores zero — so we verify before filing.

## 2026-09-17 — two candidates investigated, both refuted; invariant sweep clean

### Candidate 1 — published pages with contradictory `page_type` → NOT A BUG
- Observation: published `Webpage` records typed `error_404` whose titles are ordinary content
  (e.g. "Mild steel plate shortage on the machinist square line", `is_index: 1`).
- Test: read the `Webpage.create` schema. `page_type` is a **closed enum** and `error_404` is a
  legal value. The API allows any enum value on any page.
- Verdict: **allowed-by-design seed noise**, not a platform defect. Of 3 `error_404` pages, one is
  the genuine "Page not found" page (`is_index: 0`); the other two are mislabeled seed data.

### Candidate 2 — login vs /api/auth/me reported different roles → NOT A BUG
- Observation: an earlier `/api/auth/me` read showed roles `[website_editor, user, viewer,
  agent_user]`; a later login response showed `[website_editor, user, agent_user, website_admin,
  sales_viewer]`.
- Test: re-read `/api/auth/me` — it now **matches** the login response (`website_admin`,
  `sales_viewer`, no `viewer`).
- Verdict: our roles **changed in the shared DB between reads** — the documented "other agents
  mutate data underneath you" behaviour, not an endpoint inconsistency. Nothing to file.
- **Useful side-finding:** we now hold **`website_admin`**, which likely lets us **publish
  directly** rather than going through submit_for_review → approve_publish. Confirm during the build.

### Invariant sweep (read-only) — platform behaves as documented
| Test | Result |
|---|---|
| `Webpage.list` with an unknown argument | HTTP 200, error `-32602 "Invalid tool arguments."` (closed schema rejects — as documented) |
| `tools/call` unknown tool | HTTP 200, error `-32602 "Unknown tool."` |
| `Webpage.list` with invalid `page_type` enum value | HTTP 200, error `-32602` |
| `Webpage.list` with `limit: 999999` (schema max 1000) | HTTP 200, error `-32602` |
| `Webpage.get` with a nonexistent id | HTTP 200, error `-32602 "Not found."` |

All errors ride inside an HTTP-200 JSON-RPC envelope — exactly the documented trap. No defect.

### Where the real bugs likely are (to test during the build, not by guessing)
The classic 100-pt shape is a **write that returns success but does not change state** (the brief's
own `WorkOrder.transition` example). Our write paths — `BlogPost`/`Webpage` `create` and the
`submit_for_review → approve_publish → publish` transitions — are the place to watch. We will
exercise them in the harness with before/after DB reads and cleanup, and file anything that
silently no-ops.
