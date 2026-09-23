# Enhancement — add a page-view / traffic counter

- **Area:** Website
- **Type:** enhancement (missing feature)
- **Reported by:** Team 09
- **Submit via:** the bug-report button, description prefixed `[ENHANCEMENT]`
- **Relates to:** goal `web.pages_without_traffic` · bug N160 (`view_count` client-settable)

## Paste-ready description

> **[ENHANCEMENT] Add a page-view / traffic counter so "which pages nobody reads" is answerable from real data.**
>
> Context: the website app records no per-page view/visit data anywhere. `Webpage` has no views/visits/hits field, and `conversion_attribution` reads 0 across the whole site. So the seat goal `web.pages_without_traffic` ("which pages nobody reads") cannot be answered by reading data — it can only be approximated (e.g. orphan pages linked from no menu), with a caveat.
>
> Proposal:
> 1. Add a **system-maintained** `Webpage.view_count` (read-only to clients) that increments on each public render at `/site/{website_id}/{slug}` (and `/blog/{slug}`, `/portfolio/{slug}`).
> 2. Optionally add a lightweight `PageView` ledger (`page_id`, `website_id`, `ts`, `path`) for time-windowed queries ("reads in the last 30 days").
> 3. Expose it through `editor_capabilities` / `conversion_attribution`, or a new `endpoint.website.page_traffic`, so an agent can answer "pages with 0 views" directly.
>
> Benefit: `web.pages_without_traffic` becomes answerable from real readership instead of a reachability proxy. It also turns today's client-settable, meaningless `BlogPost.view_count` (bug N160) into a trustworthy system-maintained metric — the counter and N160's fix are the same change.
>
> Scope: website domain.
