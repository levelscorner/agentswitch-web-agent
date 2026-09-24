# Bug — `/api/website/{website_id}/rss.xml` returns HTTP 500 for every request

- **Area:** Website
- **Severity:** Low (reliability / error contract; no data disclosure observed)
- **Reported by:** Team 09
- **Status:** to file
- **Root cause class:** unhandled exception on a documented route (distinct from the validation and access-control classes we filed as N158–N160 / N219)

## Paste-ready description

> **`GET /api/website/{website_id}/rss.xml` returns HTTP 500 "Internal Server Error" for every input, while its sibling routes on the same prefix return a clean 404. The route throws before it validates the website, so it is unconditionally broken.**
>
> What I did — same `/api/website/{website_id}/*` prefix, three feed routes:
> - `GET /api/website/{id}/sitemap.xml` → **404** `{"detail":"Website not found"}`
> - `GET /api/website/{id}/robots.txt` → **404** `{"detail":"Website not found"}`
> - `GET /api/website/{id}/rss.xml` → **500** `Internal Server Error`
>
> The 500 is deterministic (3/3 repeats) and input-independent: it happens for a real website_id I own (both of my sites), for a well-formed but non-existent UUID, and for a non-UUID string like `abc`. Because every input 500s — including ids that should resolve to "not found" — the handler is erroring *before* the website lookup / not-found guard that its two siblings apply.
>
> Expected: return the same clean `404 {"detail":"Website not found"}` its siblings return (or a valid feed for a real website). A documented endpoint should not answer every request with an unhandled 500.
>
> Actual: an unhandled server error on every call. The working RSS feed is served at `/site/{website_id}/rss.xml` (HTTP 200), so the `/api/website/` RSS variant appears to be a dead/duplicate route whose handler crashes.
>
> Impact: a documented API route is 100% broken. An agent that calls it gets a 500 with no actionable error, instead of the 404 the sibling routes give — a broken error contract and a reliability defect. No stack trace or data is leaked in the body (`"Internal Server Error"` only), so security impact is low; correctness/reliability impact is real.
>
> Reproducible: yes, every request.

## Evidence (live)

```
GET /api/website/{id}/sitemap.xml  -> 404  {"detail":"Website not found"}
GET /api/website/{id}/robots.txt   -> 404  {"detail":"Website not found"}
GET /api/website/{id}/rss.xml      -> 500  Internal Server Error      (x3, identical)

rss.xml with other ids:
  suryatools (real)          -> 500 Internal Server Error
  00000000-...-000000000000  -> 500 Internal Server Error
  "abc" (not a UUID)         -> 500 Internal Server Error

Working feed for comparison:
GET /site/{id}/rss.xml       -> 200  <?xml … <rss version="2.0"> …    (len 9318)
```
