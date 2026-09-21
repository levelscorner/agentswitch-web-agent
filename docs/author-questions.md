# Questions for the author (Website seat, Team A9)

Copy-paste ready. Grouped from most to least blocking.

**Rules**
1. The "hand-written tests" rule (a test written by Claude/Codex scores zero) — does it apply
   **only to the harness tests**, or also to the **agent code** itself? (i.e. can the agent code
   be written with AI assistance as long as the tests are mine by hand?)

**Our second goal — `web.pages_without_traffic`**
2. The Website app exposes **no pageview / visitor / traffic counter** anywhere; the only
   per-page signal is `conversion_attribution`, which currently reads **0 conversions across all
   51 pages** (only 7 pages covered). How is **"traffic"** defined for this goal's predicate?
3. Is defining "pages nobody reads" as **orphan pages** (published, not in any `WebsiteMenu`, not
   linked from another page) acceptable, or is there a specific signal you expect us to use?

**Grading / verifiers**
4. Do our two goals (`web.publish_post`, `web.pages_without_traffic`) already ship a grader
   **predicate**, or do we author the verifiers ourselves? (The seat page showed empty circles.)

**Roles**
5. Our seat's roles now include `website_admin` and `sales_viewer`; an earlier check showed
   `viewer` instead. Are role sets expected to change over time? And does `website_admin` mean we
   may **publish directly** (skip submit_for_review → approve_publish)?

**Communication**
6. For a single-seat capstone, is **inter-agent email** required, or only when my seat needs
   cross-app data it cannot see (403)?

**Content**
7. For the fixture-line post — is there a product/source to reference, or should we invent
   plausible content in the house style?
