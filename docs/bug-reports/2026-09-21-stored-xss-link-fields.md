# Bug — Stored XSS: `javascript:` accepted in clickable link fields

**Seat:** Website (team09) · **Business:** Suryodaya · **Area:** website · **Severity:** High (stored XSS)

## Summary
Link fields that render as clickable `<a href>` on the public site store a `javascript:` scheme
verbatim → **stored XSS** that executes on click. Two entities confirmed:
- `WebsiteMenu.url` — renders in the **site-wide navigation** (every page).
- `PortfolioItem.project_url` — renders on the public portfolio page.

(Distinct from the filed `Webpage.og_image_url` bug: those are `href`s a visitor clicks and which
*execute*, not a meta/image tag.)

## What I did / expected / happened
- `WebsiteMenu.create { "label":"…", "website_id":"<wid>", "url":"javascript:alert(1)", "is_visible":false }`
  → stored `javascript:alert(1)`.
- `PortfolioItem.create { "title":"…", "slug":"…", "website_id":"<wid>", "project_url":"javascript:alert(1)" }`
  → stored `javascript:alert(1)`.
- **Expected:** reject non-`http(s)` schemes for any clickable link target.
- **Happened:** stored verbatim → a nav/portfolio link that runs JavaScript when clicked (cookie theft, etc.).

## Reproducible
Create the records above, confirm with `.get`. Probes kept non-live (`is_visible:false`) and the
payloads were **neutralised** afterward (overwritten to `https://example.com`). Found by
`harness/bughunt.py`.

## Ids
agent_seat: Website (team09) · Suryodaya · direct MCP `tools/call`.
