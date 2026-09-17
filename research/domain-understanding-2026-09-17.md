# Domain understanding — Suryodaya Website seat (live scrape, 2026-09-17)

Read-only scrape of our seat's live data (Suryodaya / India), to ground the gap report and
the two goals. Point-in-time; the shared DB changes.

## The business

**Suryodaya Precision Works** — precision tools / light manufacturing. Real content is about
bench vices, file sets, V-block pairs, mild-steel plate, "despatch, week NN" logs, and customer
quotes. Two websites exist under our seat:

- **Suryodaya Precision Works** — `suryodaya.co.in`
- **SuryaTools Storefront** — `suryatools.in`

## Site inventory (Suryodaya site)

| | count | breakdown |
|---|---|---|
| **Pages** (`Webpage`) | 51 | published 28 · draft 16 · review 6 · archived 1 |
| **Blog posts** (`BlogPost`) | 100 | published 36 · draft 36 · review 27 · archived 1 |
| Page types | 22 kinds | services, about, contact, blog_list, blog_post, product, portfolio, pricing, faq, gallery, team, careers, testimonials, events, landing, privacy, terms, error_404, search_results, page, custom |

## The crux: "which pages nobody reads" has no clean data source

`endpoint.website.conversion_attribution` (the only per-page signal) reports, for the whole site:

- `pages_total: 51`, `pages_published: 28`
- `paths: 8` — only **8 conversion paths exist**, covering only **7 pages**
- **`conversions_attributed: 0`** — zero conversions across the entire site
- so **44 of 51 pages have no conversion signal at all**, and the 7 that do all read zero

Consequences for the goal `web.pages_without_traffic`:

- There is **no pageview / visitor / readership counter** anywhere in the Website tools.
- The one proxy (conversions) is **zero everywhere** and measured on only 7/51 pages, so
  "pages with no conversions" is a near-useless answer (it's basically every page).
- Therefore "which pages nobody reads" is a **definition + honesty problem**, not a lookup.
  Candidate defensible definitions to evaluate against the predicate:
  1. **Orphan pages** — published pages not reachable from any `WebsiteMenu` and not linked from
     other pages (nobody *can* find them → nobody reads them). Computable from Menu + page links.
  2. **Zero-conversion pages** among those with conversion paths (weak, given all are zero).
  3. Honest **refusal/caveat** where true readership is asked for — the platform does not track it.
- This is a strong gap-report point (real analytics tools track pageviews; we don't) and a
  natural home for the required **refusal** task.

## Observation worth checking (possible bug)

Several **published** pages carry a `page_type` that contradicts the title/content, e.g. a
published page titled "Mild steel plate shortage on the machinist square line" typed
`error_404`, and content pages typed `search_results`. Could be intentional seed noise or a
seeding bug — worth a reproducing check before filing (a real bug = 100 pts; a known one = 0).

## Example real content (for concreteness)

Published pages: "Bench Vice — first article" (services), "V-Block Pair — annual review"
(blog_list), "Quote — Yashwant Alloys Pvt Ltd" (about), "Rajkot despatch, week 1" (events).

## What this means for the two goals

- **`web.publish_post`** — straightforward: `BlogPost.create` a post about the new fixture line,
  drive it to published. Real fixture/tooling content already exists to match the house style.
- **`web.pages_without_traffic`** — the hard, graded one. Pick a defensible definition (orphan
  pages is the strongest), compute it from the API, and state the definition + its limits.
