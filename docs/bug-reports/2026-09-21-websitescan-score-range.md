# Bug — WebsiteScan audit scores accept out-of-range values

**Seat:** Website (team09) · **Business:** Suryodaya · **Area:** website / WebsiteScan · **Severity:** Medium (data integrity)

## Summary
The four audit scores (`performance_score`, `seo_score`, `accessibility_score`,
`best_practices_score`) are 0–100 metrics, but the API stores out-of-range and negative values, and
they are client-settable with no real crawl, so scan quality can be fabricated. Distinct from the
filed `sitemap_priority` (0–1) bug: new entity, explicit 0–100 bounds.

## What I did / expected / happened
- `WebsiteScan.create { "url":"https://example.com", "website_id":"<wid>", "performance_score":9999,
  "seo_score":-50, "accessibility_score":250, "best_practices_score":-1 }`
  → stored `performance_score=9999.0`, `seo_score=-50.0`, etc.
- **Expected:** constrain each score to 0–100 (reject or clamp); scores should be server-derived from
  a real scan, not client-set.
- **Happened:** stored verbatim, out of range and negative.

## Reproducible
Create the scan, confirm with `WebsiteScan.get`. Found by `harness/bughunt.py`.

## Ids
agent_seat: Website (team09) · Suryodaya · direct MCP `tools/call`.
