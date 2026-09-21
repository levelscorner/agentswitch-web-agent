# Bug — Open redirect: `WebsiteRedirect.to_path` accepts an external URL

**Seat:** Website (team09) · **Business:** Suryodaya · **Area:** website / WebsiteRedirect · **Severity:** Medium-High (open redirect / phishing)

## Summary
`to_path` is meant to be an internal site path, but it accepts an absolute **external** URL. That
turns an internal SEO redirect into an **open redirect** an attacker can use for phishing
(`suryodaya.co.in/x` → `https://evil.example.com/phish`). Distinct from the filed self-loop bug on the
same entity (different vuln class).

## What I did / expected / happened
- `WebsiteRedirect.create { "website_id":"<wid>", "from_path":"/x", "to_path":"https://evil.example.com/phish", "is_active":false }`
  → stored `https://evil.example.com/phish`.
- **Expected:** restrict `to_path` to a site-relative internal path (or an explicit allow-list); reject
  external hosts and unsafe schemes.
- **Happened:** stored verbatim → a link on our domain silently forwards visitors to any external site.

## Reproducible
Create the redirect with `is_active:false` (dormant), confirm with `WebsiteRedirect.get`. Found by
`harness/bughunt.py`.

## Ids
agent_seat: Website (team09) · Suryodaya · direct MCP `tools/call`.
