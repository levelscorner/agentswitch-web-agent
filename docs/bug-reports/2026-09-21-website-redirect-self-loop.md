# Bug — WebsiteRedirect accepts a self-redirect (infinite loop)

**Seat:** Website (team09) · **Business:** Suryodaya — `agentswitch.theschoolofai.in`
**Area:** website / WebsiteRedirect · **Severity:** Medium (broken routing)

## Summary
`WebsiteRedirect.create` accepts a rule whose `from_path` equals its `to_path`. A visitor hitting
that path is redirected to itself forever, an **infinite redirect loop** (browsers stop with
"ERR_TOO_MANY_REDIRECTS"). The API should reject `from_path == to_path`.

## What I did / expected / happened
- `WebsiteRedirect.create { "website_id": "<wid>", "from_path": "/x", "to_path": "/x" }`
  → **created** (a redirect from `/x` to `/x`). Expected: reject (a redirect to itself is never valid).

## Why it matters
Any visitor (or crawler) reaching that path gets an infinite loop and the page is unreachable.

## Reproducible
Create a redirect with `from_path == to_path`; confirm with `WebsiteRedirect.get`. Found +
reproduced by `python3 -m harness.bughunt --run` (`hunt_redirect`). Test rules left inactive.

## Ids
agent_seat: Website (team09) · Suryodaya · direct MCP `tools/call`.
