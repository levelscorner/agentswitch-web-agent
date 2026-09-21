# Bug — BlogPost.view_count is client-settable, and numeric fields skip validation

**Seat:** Website (team09) · **Business:** Suryodaya — `agentswitch.theschoolofai.in`
**Area:** website / BlogPost · **Severity:** Medium (data integrity / trust)

## Summary
`view_count` (the "how many times this post was viewed" counter) can be set to **any** value by
the creating/editing user, on **both** `BlogPost.create` and `BlogPost.update`, and it even
accepts **negative** numbers. A counter a user can hand-set (and make negative) is not
trustworthy. The related field `reading_time_minutes` also accepts negatives. The **same class of
defect** appears on `WebsiteRedirect.hit_count` (also fully client-settable, e.g. `999999`), so
analytics counters across the Website app are user-controlled rather than system-maintained.

## What I did / expected / happened
1. `BlogPost.create { ..., "view_count": 777777 }` → stored **`777777.0`**.
   *Expected:* view_count starts at 0 and is only raised by the system on a real view; an editor
   should not be able to set it.
2. `BlogPost.update { "id": ..., "view_count": 555555 }` → stored **`555555.0`** (writable after create too).
3. `BlogPost.create { ..., "view_count": -42 }` → stored **`-42.0`**. A view count can never be negative.
4. `BlogPost.create { ..., "reading_time_minutes": -9 }` → stored **`-9.0`**. Reading time can't be negative.

## Why it matters
- Analytics a user can set (and even make negative) are untrustworthy; "most-viewed posts"
  rankings can be gamed.
- Directly relevant to the Website seat's job (page/post traffic): any readership metric built on
  `view_count` is unreliable.
- Secondary: these counts are stored as **floats** (`777777.0`); counts should be integers.

## Reproducible
Any `BlogPost.create`/`update` with `view_count = N` (including negative) stores `N`; confirm
with `BlogPost.get`. Found + reproduced by `python3 -m harness.bughunt --run`. All test rows
were cleaned up (unpublished + archived).

## Ids
agent_seat: Website (team09) · Suryodaya · direct MCP `tools/call` (no job id).
