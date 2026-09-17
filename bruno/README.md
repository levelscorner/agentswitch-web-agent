# Bruno collection — AgentSwitch Team09 Website

A git-friendly API client for poking the platform by hand. Bruno stores every request
as a plain `.bru` text file, so this whole collection is version-controlled in the repo.

## Open it

1. Launch **Bruno** (already installed at `/Applications/Bruno.app`).
2. **Open Collection** -> pick this folder: `s20-capstone-agentswitch/bruno`.
3. Top-right environment dropdown -> choose **Suryodaya** (India) or **Keystone** (US).

## One-time secret (your password never lands in git)

`password` is declared as a **secret variable** in each environment, so its value is NOT
written to the `.bru` files. Set it once per environment:

- Click the environment name -> **Configure** -> set `password` to your team password
  (Suryodaya password for the Suryodaya env, Keystone password for Keystone).
- Bruno stores secret values locally, outside the repo.

## Run order

1. **01 Login** — logs in and, via its post-response script, stashes the `token` into the
   environment automatically. Run this first (and again whenever the token expires).
2. **02 Who am I** — confirms the seat (should show team09 / website).
3. **03 MCP initialize**, **04 MCP tools_list** — the handshake + our 236-tool catalogue.
4. **05-08** — real `tools/call` examples: `Website.list`, `Webpage.list`, `BlogPost.list`,
   and `conversion_attribution` (the per-page "traffic"/conversion signal).

Every request after Login uses `Authorization: Bearer {{token}}` automatically — no CSRF
header needed on the Bearer path (that was only the browser cookie shortcut).

## Add your own

Copy any `.bru` file, change the `tools/call` `name` + `arguments`, done. The full tool
list and schemas are in `../notes/website-capabilities.md`.
