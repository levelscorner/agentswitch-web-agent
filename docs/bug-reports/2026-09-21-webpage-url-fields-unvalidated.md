# Bug — Webpage URL fields accept invalid / unsafe values (no URL validation)

**Seat:** Website (team09) · **Business:** Suryodaya — `agentswitch.theschoolofai.in`
**Area:** website / Webpage · **Severity:** Medium (SEO + unsafe scheme)

## Summary
Webpage URL fields are not validated. `canonical_url` accepts a plain non-URL string, and
`og_image_url` accepts a `javascript:` scheme. Validation is applied **inconsistently** — `slug`
*is* sanitised (see below), but these URL fields are stored verbatim.

## What I did / expected / happened
- `Webpage.create { ..., "canonical_url": "not a real url at all" }` → stored verbatim.
  Expected: require a valid absolute URL; a malformed canonical breaks SEO canonicalisation.
- `Webpage.create { ..., "og_image_url": "javascript:alert(1)" }` → stored verbatim.
  Expected: reject non-`http(s)` schemes; `javascript:` is an unsafe scheme in a URL field.
- (For contrast: `slug` "Bad Slug !@# CAPS" was correctly sanitised to `bad-slug-...-caps`, so the
  platform *does* validate some fields, just not these URL ones.)

## Why it matters
- A malformed `canonical_url` breaks canonicalisation (SEO harm).
- Accepting `javascript:` (and other unsafe schemes) where an image URL is expected is a
  validation/security gap.

## Reproducible
`Webpage.create`/`update` with the values above; confirm with `Webpage.get`. Found + reproduced by
`python3 -m harness.bughunt --run`. Test pages cleaned up (archived).

## Ids
agent_seat: Website (team09) · Suryodaya · direct MCP `tools/call`.
