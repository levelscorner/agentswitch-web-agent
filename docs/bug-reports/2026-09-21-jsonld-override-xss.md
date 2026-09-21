# Bug — Stored XSS: `Webpage.json_ld_override` allows `</script>` breakout

**Seat:** Website (team09) · **Business:** Suryodaya · **Area:** website / Webpage · **Severity:** High (stored XSS)

## Summary
`json_ld_override` is emitted verbatim inside a `<script type="application/ld+json">` block. A value
containing `</script>` closes that element early and injects an executable `<script>` → **stored XSS**
on the rendered page. Distinct mechanism from the URL-scheme bugs (script-tag breakout, not a URL).

## What I did / expected / happened
- `Webpage.create { "title":"…", "slug":"…", "website_id":"<wid>", "json_ld_type":"Article",
  "json_ld_override":"</script><script>alert(1)</script>" }` → stored verbatim.
- **Expected:** validate `json_ld_override` as well-formed JSON and reject / escape anything that can
  close the JSON-LD `<script>` element.
- **Happened:** stored as-is → renders as a breakout `<script>` on the page.

## Reproducible
Create the page (left unpublished, then archived), confirm with `Webpage.get`. Found by
`harness/bughunt.py`.

## Ids
agent_seat: Website (team09) · Suryodaya · direct MCP `tools/call`.
