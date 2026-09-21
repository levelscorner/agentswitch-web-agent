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

## 2026-09-21 — write-path hunt (`harness/bughunt.py`, live)

| Probe | Result |
|---|---|
| create → read back | row persists as draft ✅ |
| publish → read back | status flips to `published`, `published_at` set ✅ |
| duplicate slug | platform auto-uniquifies (`slug` → `slug-2`) ✅ — a **false positive** until we compared the returned slugs (verify before filing) |
| `approve_publish` a never-submitted draft | rejected ✅ |
| `approve_publish` own draft | rejected — needs a **second person** (separation of duties) ✅ → our Publisher uses direct `BlogPost.publish` (allowed by `website_admin`) |
| `status='published'` on create | ignored, stored `draft` ✅ (no bypass) |
| **`view_count` injected on create** | **stored verbatim (`777777.0`) → FILED** — client-settable analytics |

Net: write paths are well-built. One real bug: **`BlogPost.view_count` is client-settable** —
see `docs/bug-reports/2026-09-21-blogpost-view-count-settable.md`.

## 2026-09-21 — round 2 (numeric validation)

| Probe | Result |
|---|---|
| `view_count` via `update` | settable (555555) — strengthens bug #1 |
| `view_count` negative | `-42` accepted — a count can't be negative |
| `reading_time_minutes` negative | `-9` accepted |
| **`Webpage.sitemap_priority` = 99 / -5** | **accepted → FILED (bug #2)** — sitemap spec is 0.0-1.0 → invalid sitemap |
| `BlogPost.published_at` backdated (1999) | accepted, but likely intended (scheduled date) — not filed |

**Two filed bugs:** view_count (`docs/bug-reports/…view-count-settable.md`) and
sitemap_priority (`…sitemap-priority-range.md`).
**Lead for round 3:** `WebsiteRedirect.hit_count` — same analytics-counter family as view_count;
and `from_path == to_path` self-redirect.

## 2026-09-21 — round 3 (WebsiteRedirect)

| Probe | Result |
|---|---|
| `WebsiteRedirect.hit_count` = 999999 | accepted → folded into bug #1 (analytics counters settable) |
| `WebsiteRedirect` `from_path == to_path` | **accepted → FILED (bug #3)** — infinite redirect loop |

**Three filed bugs so far:**
1. Analytics counters client-settable + unvalidated (`view_count`, `hit_count`; negatives) — `…view-count-settable.md`
2. `Webpage.sitemap_priority` out of range → invalid sitemap — `…sitemap-priority-range.md`
3. `WebsiteRedirect` self-redirect loop — `…website-redirect-self-loop.md`

All reproducible via `python3 -m harness.bughunt --run`.

**FILED 2026-09-21** (`POST /api/bug-report`, HTTP 201; `GET /api/bug-report/mine` confirms 3):
- `7d6cd211-c744-4f57-80b2-dc04e0c97fac` — analytics counters client-settable (view_count / hit_count)
- `f8d458bc-152c-4047-81d3-6d30685cc962` — Webpage.sitemap_priority out of range
- `e5d0803a-37a0-4d41-96be-8e5eb88ac7e6` — WebsiteRedirect self-redirect loop
