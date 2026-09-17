# Setup — dot by dot

Everything we set up to go from "we have a seat" to "we can drive the platform and test it."
Nothing here stores a secret; every password/token stays in a git-ignored place.

---

## 0. What we are connecting to

- **AgentSwitch** is a live, hosted business platform the course runs. We do **not** host or
  build it. We drive it over the network.
- It exists as **two businesses** (same software, two jurisdictions):
  - **Suryodaya Precision Works** — India — `https://agentswitch.theschoolofai.in` (we start here)
  - **Keystone Precision Works LLC** — US — `https://class.agentswitch.theschoolofai.in`
- We are **Team 09, the Website seat**. Our login: `team09@theschoolofai.in`, one password
  **per business** (from our team channel — never committed).

---

## 1. Local shell config (`.env`)

- `.env.example` is the committed template. Copy it once: `cp .env.example .env`.
- `.env` is **git-ignored** — it is the only place the password lives on disk, and it never
  leaves your machine.
- What it holds:
  - `AS_BASE` — which business (Suryodaya by default).
  - `AS_EMAIL` — `team09@theschoolofai.in`.
  - `AS_PASSWORD` — you paste this; blank in the template.
  - `AS_WEBSITE_SURYODAYA` / `AS_WEBSITE_SURYATOOLS` — the two website IDs we discovered.
  - `GEMINI_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` — the agent's own model key (later).
- Load it into a shell with `set -a; source .env; set +a`.

## 2. `probe.py` — the read-only smoke test

- Zero dependencies (standard-library `urllib` only).
- What it does, in order: **login** (`/api/auth/login` -> Bearer token) → **who am I**
  (`/api/auth/me`) → **MCP `initialize`** → **MCP `tools/list`** → **`/api/schemas`**.
- It writes the raw responses to `probe-out/` (git-ignored) and prints a short summary.
- It **never prints or stores the token**, and it **creates/changes nothing** on the platform.
- Run: `set -a; source .env; set +a; python3 probe.py`.

## 3. Bruno — the by-hand API client (`bruno/`)

Bruno is like Postman but stores every request as a plain-text `.bru` file, so the whole
collection is version-controlled in this repo.

- Open **Bruno** → **Open Collection** → select the `bruno/` folder.
- Pick an **environment** (top-right): **Suryodaya** (India) or **Keystone** (US).
- Set the `password` **secret** variable once per environment (Configure → password). Secret
  values are stored by Bruno locally, **never written to the `.bru` files**.
- Run order:
  1. **01 Login** — logs in and auto-stashes the `token` into the environment (post-response script).
  2. **02 Who am I** — confirms the seat.
  3. **03 MCP initialize**, **04 MCP tools_list** — handshake + our 236-tool catalogue.
  4. **05–08** — real `tools/call` examples: `Website.list`, `Webpage.list`, `BlogPost.list`,
     `conversion_attribution`.
- Every request after Login sends `Authorization: Bearer {{token}}` automatically.

---

## 4. The auth model we figured out (important)

There are **two ways in**, and they behave differently:

- **Bearer token (what our agent + probe.py + Bruno use).**
  `POST /api/auth/login` with email + password returns `{ "token": "..." }`. Send that as
  `Authorization: Bearer <token>` on every call. **No CSRF token needed.** This is the
  documented, canonical path.
- **Browser session (only used for our manual poking in the logged-in web app).**
  The web app authenticates with a **cookie** plus a `csrf_token` cookie that must be echoed
  back in an **`X-CSRF-Token`** header. Without that header, `/api/mcp` returns **403** — which
  looks like a permission error but is really CSRF. Our agent does **not** use this path.

Trap to remember for both: a **JSON-RPC error still returns HTTP 200**; the failure is inside
the response envelope. Only real auth failures answer at the HTTP layer (`401`).

---

## 5. The connection tests we ran, and what each proved

| Test | Result | What it told us |
|---|---|---|
| `GET /api/auth/me` | 200 | We are `team09`, roles `website_editor,user,viewer,agent_user`, `allowed_apps = website, agent, crm`. |
| MCP `tools/list` | 236 tools | Our seat's full capability surface (62 entity families + 35 app endpoints). |
| Filter to website tools | 36 tools | `Webpage.*` and `BlogPost.*` have full publish workflows (create → submit → approve → publish). |
| `Website.list` | 2 sites | `suryodaya.co.in` and `suryatools.in`, with their IDs. |
| `endpoint.website.conversion_attribution` | per-page data | Conversions/outcomes per page + section — the only "engagement" signal. |
| `Webpage.list` fields | no view field | **There is no raw page-view counter.** "No traffic" must be defined (zero conversions) or honestly refused. |
| `endpoint.website.editor_capabilities` | `can_create_page: true` | Our role may create pages. Publish-vs-review path still to pin down. |

The full capability map (all families, the 36 website tools, the two goal IDs, the traffic
finding) is in [`../notes/website-capabilities.md`](../notes/website-capabilities.md).
