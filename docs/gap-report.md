# Gap Report — AgentSwitch Website seat vs. real AI-native publishing + analytics

Week-1 deliverable. **Team A9 · Seat 09 · Website.** Compares our seat to the best real products
doing our job, and separates what an agent can close today from what needs platform work.

**The crux.** Our graded job: *"Publish a post about the new fixture line, and tell me which
pages nobody reads."* We can publish. We **cannot** truthfully answer the second half:
AgentSwitch stores **no pageview / visitor / traffic data anywhere**. The only per-page signal,
`conversion_attribution`, reports outcomes (form submits, bookings) — and on our live Suryodaya
site it reads **0 conversions attributed across all 51 pages**, with only **7 pages** covered at
all. Every product below answers "which pages nobody reads" with **native raw-traffic analytics** —
the exact dataset we lack.

## 1. What they do that we do not

- **Ghost — native per-post view analytics** (the precise missing capability). Ghost 6.0 (Aug
  2025) ships built-in, cookie-free web analytics: each post shows **Unique visitors** and
  **Total views**, the post list ranks published posts by traffic, and the last 1,000 posts export
  to CSV. Ghost also matches our content model (posts/pages) and a draft → published workflow, and
  is fully agent-drivable via its **Admin API** (`POST /admin/posts/`, draft or published) +
  Content API. We store zero views, so we have no equivalent.
- **Plausible — "dead pages" is a first-class report.** Top Pages / Entry Pages / Exit Pages
  (Visitors, Pageviews, Bounce, Time on Page), sortable to surface low/no-traffic pages, exposed via
  a read-only **Stats API** (`/api/v2/query`, group by `event:page`). We would be sorting a
  conversions table that 44 of 51 pages never touch.
- **Fathom — the same answer via API.** Reports API groups by `pathname` and aggregates
  `visits, uniques, pageviews, avg_duration, bounce_rate`. Raw traffic per URL we have no field for.
- **Rillet — the course's MCP bar, already met on our side.** Rillet ships an official remote
  **MCP server** over its ledger. Our seat is likewise an MCP over Pages / Blog / Scans /
  Conversions — so the parity gap is **not the protocol**, it is the missing traffic dataset.

## 2. Which gaps an agent can close vs. which need platform work

| Gap | Agent closes it (orchestration, ours) | Needs a new platform table/endpoint (theirs) |
|---|---|---|
| Publish the fixture-line post | ✅ `BlogPost.create` → `submit_for_review` → `approve_publish` / `publish`; set menus/redirects; `WebsiteScan` the new URL | — |
| Rank pages by *outcome* | ✅ `conversion_attribution` joined to Pages; flag zero-outcome pages | — |
| **"Which pages nobody reads" (real traffic)** | ⚠️ only a conversions proxy — misleading (a well-read info page with no form reads zero) | ❌ **a `PageView`/traffic table + an ingest pixel + a top-pages query API.** No orchestration invents visitor data never collected |
| "Thin / low-value pages" | ✅ `WebsiteScan` SEO grade per URL (partial substitute) | ❌ scans grade content, not whether humans visited |

**Bottom line:** the publish half is fully agent-closeable today; the "dead pages" half is
**platform work** — one missing primitive (pageviews). Conversion is not readership, so our
current data can only approximate it, and wrongly.

## 3. What an agent can do that their UIs cannot

- **Hold the compound goal across many steps.** Ghost / Plausible / Fathom are dashboards a human
  reads and stitches together. Our agent holds "*publish X **and** find dead pages*" as one
  objective: publish through the review workflow, pull attribution, **re-read the changed site
  state**, cross-reference pages, and return one ranked answer.
- **Decide and act, not just display.** Their stats APIs are read-only; our agent chains
  read → reason → write in one loop (publish, scan, attribute, then draft redirects for the
  losers), mirroring Rillet's "ask, then act on live data" — once the traffic data exists.

## What this means for our build

- **`web.publish_post`** — build it; fully supported.
- **`web.pages_without_traffic`** — **define it honestly.** Strongest defensible definition given
  no view data: **orphan pages** (published pages not in any `WebsiteMenu` and not linked from other
  pages, so unreachable and unread), with an explicit caveat that true readership is not tracked.
  This is also our natural **refusal** task: asked for real readership, the agent must say the
  platform does not record it rather than pass off conversions as reads.

## Sources

- Ghost post analytics (unique visitors / views, CSV export) — https://ghost.org/help/post-analytics/
- Ghost 6.0 native analytics — https://ghost.org/changelog/6/
- Ghost Admin API, create post (draft or published) — https://docs.ghost.org/admin-api/posts
- Plausible Top / Entry / Exit Pages — https://plausible.io/blog/analyzing-landing-pages
- Plausible read-only Stats API — https://plausible.io/docs/stats-api
- Fathom Reports API — https://usefathom.com/api/v1/reports
- Rillet official MCP server — https://docs.api.rillet.com/docs/mcp

_Note: none of Ghost / Plausible / Fathom ships an official MCP today (Ghost = community + open
proposal; Plausible / Fathom = community servers), but all three expose official REST/Stats APIs an
agent can drive, so the "agent-drivable" claim holds even where "MCP-native" does not._
