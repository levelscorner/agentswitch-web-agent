# Bug — Webpage.sitemap_priority accepts out-of-range values (invalid sitemap)

**Seat:** Website (team09) · **Business:** Suryodaya — `agentswitch.theschoolofai.in`
**Area:** website / Webpage · **Severity:** Low–Medium (SEO / spec compliance)

## Summary
`sitemap_priority` sets a page's `<priority>` in `sitemap.xml`. The sitemaps.org spec requires a
value **between 0.0 and 1.0**. The API accepts `99` and `-5`, producing an **invalid sitemap** that
crawlers ignore or reject.

## What I did / expected / happened
- `Webpage.create { ..., "sitemap_priority": 99 }` → stored **`99.0`**. Expected: reject or clamp to `0.0-1.0`.
- `Webpage.create { ..., "sitemap_priority": -5 }` → stored **`-5.0`**. Expected: reject (negative is invalid).

## Why it matters
A `sitemap.xml` with `<priority>` outside `0.0-1.0` is invalid per the sitemaps.org spec; search
engines ignore the value (or the entry). For the Website seat this is a direct SEO concern.

## Reproducible
`Webpage.create` with `sitemap_priority` = `99` or `-5`, confirm with `Webpage.get`. Found +
reproduced by `python3 -m harness.bughunt --run` (`hunt_webpage`). Test pages cleaned up.

## Ids
agent_seat: Website (team09) · Suryodaya · direct MCP `tools/call`.
