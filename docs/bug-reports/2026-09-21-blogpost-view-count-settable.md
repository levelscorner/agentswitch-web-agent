# Bug — BlogPost.view_count is client-settable (fabricated analytics)

**Seat:** Website (team09) · **Business:** Suryodaya — `agentswitch.theschoolofai.in`
**Area:** website / BlogPost · **Severity:** Medium (data integrity / trust)

## What I did
Called `BlogPost.create` with an explicit `view_count`, then read the row back:

```
BlogPost.create { "title": "...", "slug": "inj-<ts>", "website_id": "<wid>",
                  "content": "x", "view_count": 777777 }
BlogPost.get { "id": "<new id>" }
```

## What I expected
`view_count` is an analytics counter (how many times a post was viewed). A creating user
should **not** be able to set it — it should start at 0 and only be incremented by the system
when the post is actually viewed.

## What happened
The row stored **`view_count = 777777`** (and as a float: `777777.0`). Any user with create
rights can set a post's view count to any value. The same field is writable, so
`BlogPost.update` almost certainly allows it too.

## Why it matters
- Analytics a user can hand-set are not trustworthy; "most-viewed posts" can be gamed.
- Secondary defect: a view **count** is stored as a **float** (`777777.0`); counts are integers.

## Reproducible
1. `BlogPost.create` with any `view_count` (e.g. 777777).
2. `BlogPost.get` the new id → `view_count` equals what you sent.
3. (cleanup) `BlogPost.unpublish` + `BlogPost.archive`.

Found + reproduced by our harness: `python3 -m harness.bughunt --run`.

## Ids
agent_seat: Website (team09) · page: n/a · job: n/a (direct MCP `tools/call`).
