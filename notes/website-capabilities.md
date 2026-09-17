# Website seat — live capability map (Suryodaya / India)

Captured 2026-09-17 by driving the logged-in session over MCP (`tools/list` + read-only
`tools/call`). Read-only: nothing was created or changed. No secrets in this file.

## Connection (how the calls actually authenticate)

- **Base:** `https://agentswitch.theschoolofai.in`  (Keystone/US: `https://class.agentswitch.theschoolofai.in`)
- **Identity:** `GET /api/auth/me` → seat, cookie-authenticated in the browser.
- **MCP:** `POST /api/mcp`, JSON-RPC 2.0.
  - Browser session (what we used to probe): cookie auth **plus** the `csrf_token` cookie
    echoed back in an **`X-CSRF-Token`** header. Without it, `/api/mcp` returns **403**
    (not 401) — worth remembering, it looks like a permission error but it's CSRF.
  - **Our agent** will instead use `POST /api/auth/login` → **Bearer token** (no CSRF needed),
    which is the path the brief documents. Cookie+CSRF is only our manual-probe shortcut.

## Our seat (from /api/auth/me)

- email `team09@theschoolofai.in`, name "Team 09"
- roles: `website_editor, user, agent_user, website_admin, sales_viewer` (as of 2026-09-17 20:00;
  an earlier read showed `viewer` instead of the two admin/sales roles — **roles change in the
  shared DB**). **`website_admin` likely permits direct `publish`** rather than only
  submit_for_review → approve_publish; confirm during the build.
- allowed_apps: **website, agent, crm**
- company_id `5cbe5a55-af74-4363-a436-f5350593114c`

## Scale of our catalogue

- **236 MCP tools** visible to our seat, across **62 entity families** + **35 app endpoints**.
- Beyond `website`, our seat also sees `agent` (our own workspace: AgentMemory, AgentSkill,
  AgentTask, AgentSession, AgentPersona, AgentRunbook, AgentTodo, …) and `crm` (Party,
  AddressBook, ContactGroup, …), plus shared Drive/File/Notification/Privacy families.

## The 36 Website-domain tools

**Webpage** (full editorial workflow): `Webpage.list/.get/.create/.update` +
`.submit_for_review / .approve_publish / .request_changes / .publish / .unpublish /
.archive / .restore`. Plus `WebpagePublication.get/.list` and `WebpageRevision.get/.list`.

**BlogPost** (same workflow, 11 tools): `BlogPost.list/.get/.create/.update /
.submit_for_review / .approve_publish / .request_changes / .publish / .unpublish /
.archive / .restore`. Plus `BlogCategory.create/.get/.list/.update`.

**Other site objects:** `PortfolioItem.*`, `Website.get/.list/.update`,
`WebsiteMenu.*`, `WebsiteRedirect.*`, `WebsiteScan.create/.get/.list`,
`CompanyBranding.get/.list/.update`.

## The 12 Website app endpoints (`endpoint.website.*` + public)

`preview_products`, `accessibility_check`, `publication_plan`, `publication_request`,
`publication_sweep`, **`conversion_attribution`**, **`editor_capabilities`**, plus
`endpoint.public.collective.*` and `endpoint.email.public.subscriber_lists`.

- `editor_capabilities({website_id})` → `{can_create_page: true, ok: true}` for us.
- `conversion_attribution({website_id})` → per-page + per-section **conversion** data:
  `paths[]` each with `page_id, page_slug, page_title, page_status, section_component,
  section_conversions, outcome_count, outcome_entity, cta_links, attribution, …`, plus
  honest `missing_columns` notes on what is and isn't attributable.

## Our two websites

| name | domain | id |
|---|---|---|
| SuryaTools Storefront | suryatools.in | `3b417d55-0a29-4bae-86ee-3ce5efbe375d` |
| Suryodaya Precision Works | suryodaya.co.in | `dfca595d-4248-4b07-988f-fcfbd3f3caf1` |

## The task, mapped to real tools

Graded request: *"Publish a post about the new fixture line, and tell me which pages nobody reads."*

**The two evaluator goal IDs for our seat (from the seat page):**
- `web.publish_post` — publish a post about the new fixture line
- `web.pages_without_traffic` — which pages get no traffic?

Only 15 of 63 goals ship with a course predicate; an empty circle on the seat page means
no predicate verifies it yet — that verifier is our harness work. Note the goal says
"no **traffic**", but the platform exposes no raw pageview counter (see finding below), so
the defensible definition of "traffic" is itself part of the graded work.

1. **Publish a post** → `BlogPost.create` then reach published state via
   `BlogPost.submit_for_review` → `BlogPost.approve_publish` (or `BlogPost.publish` if our
   role may publish directly — `editor_capabilities` says we can create; the publish-vs-review
   path is the next thing to pin down per role).
2. **"Which pages nobody reads"** → **big finding: there is no raw page-view / read-count
   field anywhere.** `Webpage` records carry no `views/visits/hits`. The only engagement
   signal the platform exposes is **`conversion_attribution`** (conversions/outcomes per
   page+section). So "nobody reads" must be defined as **pages with zero conversions /
   attributed outcomes**, and the agent should *say* that is the definition it used — or,
   where even that can't be supported, refuse/caveat honestly. This is precisely the
   judgement-call + honest-limits behaviour the brief grades.

## Immediate next steps

- Pin down the publish path for `website_editor` (direct `publish` vs. `submit_for_review`
  → someone approves). Try it in the harness, not by guessing.
- Decide + document the working definition of "nobody reads" (zero-conversion pages via
  `conversion_attribution`), and design a refusal/caveat task around the missing view data.
- Have `probe.py` (Bearer auth) dump `tools/list` + schemas to `probe-out/` for a durable,
  greppable copy of all 236 tool schemas.
