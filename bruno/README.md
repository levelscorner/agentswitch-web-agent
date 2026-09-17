# Bruno collection — AgentSwitch Team09 Website

A git-friendly API client for poking the platform by hand. Every request is a plain `.bru`
text file, so the whole collection is version-controlled.

## Open it

1. Launch **Bruno** (installed at `/Applications/Bruno.app`).
2. **Open Collection** -> pick this `bruno/` folder.
3. Top-right environment dropdown -> choose **Suryodaya** (India) or **Keystone** (US).

## Environment variables

Both environments define the same variables:

- `email` — team09@theschoolofai.in
- `ASIND` — India base URL (https://agentswitch.theschoolofai.in)
- `ASUSA` — US base URL (https://class.agentswitch.theschoolofai.in)

plus two **secret** variables (values stored locally by Bruno, never committed to git):

- `password` — your team password (India password in the Suryodaya env, US in Keystone)
- `token` — filled automatically by the Login request's post-response script

## Requests target India by default

Every request uses `{{ASIND}}` (the India / Suryodaya base). Pair it with the **Suryodaya**
environment so the login password matches the URL. To hit the US business, switch the request
URLs to `{{ASUSA}}` and select the **Keystone** environment.

## Run order

1. **01 Login** — logs in and stashes `token`. Run this first (and again when it expires).
2. **02 Who am I** — confirms the seat (team09 / website).
3. **03 / 04** — MCP `initialize` + `tools/list` (our 236-tool catalogue).
4. **05-08** — `tools/call` examples: `Website.list`, `Webpage.list`, `BlogPost.list`,
   `conversion_attribution`. (Webpage/conversion use the Suryodaya website id inline.)

Every request after Login sends `Authorization: Bearer {{token}}` automatically — no CSRF
header on the Bearer path.

## Add your own

Copy any `.bru`, change the `tools/call` `name` + `arguments`. Full tool list + schemas are in
`../notes/website-capabilities.md`.
