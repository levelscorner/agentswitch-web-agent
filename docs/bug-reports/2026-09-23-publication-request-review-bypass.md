# Bug — `publication-request` bypasses the two-person review guard (segregation of duties)

- **Area:** Website
- **Severity:** High
- **Reported by:** Team 09
- **Status:** to file
- **Root cause class:** broken access control / workflow integrity (distinct from the field-validation bugs N158/159/160)

## Paste-ready description

> **`POST /api/website/publication-request` publishes a webpage that the same seat created AND submitted for review, bypassing the segregation-of-duties rule the transition engine enforces.**
>
> What I did:
> 1. `Webpage.create` → a draft page (created_by = my seat).
> 2. `Webpage.submit_for_review` → status becomes `review`.
> 3. `Webpage.approve_publish` → **REJECTED**: "Transition 'Approve & Publish' cannot be performed by the same [creator]" — the `actor_not: created_by` guard, working as intended.
> 4. `POST /api/website/publication-request { "webpage_id": <same page> }` → **200 OK**, `result.action = "schedule"`, and the page status became **`published`**.
>
> Expected: `publication-request` should enforce the same `actor_not: created_by` / approval rule as the `approve_publish` transition — a page must not be published by the seat that submitted it without a second reviewer.
>
> Actual: the page went `review → published`, published by its own submitter, with no second party. The review gate is enforced on the transition path but **not** on the `publication-request` endpoint — two publish paths, only one guarded.
>
> Impact: the two-person review control is fully bypassable. A single editor can author, submit, and publish content to the public `/site/{website_id}/…` pages with no oversight. This composes with the stored-XSS link/field bugs (N158) — one account can push malicious content live unreviewed.
>
> Scope note: `endpoint.website.publication-sweep` (the batch variant) likely shares this root cause and should be checked.
>
> Reproducible: yes, every run.

## Evidence (live)

```
1) created draft:               draft
2) after submit_for_review:     review
3) approve_publish (same seat):  REJECTED [-32602] "cannot be performed by the same [creator]"
   status still:                review
4) POST /api/website/publication-request { webpage_id }  -> [200] result.action="schedule"
   FINAL status =               published
```
