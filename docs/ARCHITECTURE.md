# Architecture — the graph, with code and data flow

Three views: **who talks to whom** (components), **how we authenticate** (auth flow), and
**how the graded task moves through the system** (data flow). Then the harness loop that scores it.

---

## 1. Components — who talks to whom

```mermaid
flowchart LR
  subgraph local["Your machine (this repo)"]
    direction TB
    agent["Web Agent<br/>perceive → decide → act loop"]
    tools["MCP client<br/>login + tools/call"]
    harness["Harness<br/>tasks + verifiers"]
    probe["probe.py"]
    bruno["Bruno"]
    agent --> tools
  end
  model[("LLM provider<br/>your key")]
  subgraph hosted["AgentSwitch (hosted by the course)"]
    direction TB
    mcp["POST /api/mcp<br/>JSON-RPC 2.0"]
    rest["REST + app endpoints"]
    db[("Shared database")]
    eval["Evaluator predicates"]
    mcp --> db
    rest --> db
    eval --> db
  end

  agent -->|"prompts + decisions"| model
  tools -->|"Bearer token"| mcp
  harness -->|"runs the agent"| agent
  harness -->|"reads DB state to verify"| rest
  harness -->|"scores against"| eval
  probe -->|"read-only"| mcp
  bruno -->|"manual"| mcp
```

**Nodes**

- **Web Agent** — our code. One loop: read state → decide the next step → call a tool → repeat
  until the goal is met. Runs on our machine with our model key.
- **MCP client** — the thin layer that logs in, holds the Bearer token, and makes `tools/call`
  requests. This is the agent's only door to the platform.
- **Harness** — our test rig. Runs the agent on a task set and, crucially, **verifies by reading
  the database**, not by reading the agent's reply. Saves every run to disk before scoring.
- **probe.py / Bruno** — exploration tools. Not part of the running agent; they help us learn
  and debug the API by hand.
- **AgentSwitch (hosted)** — the platform. Same database and permission rules behind MCP, REST,
  and the web UI. The **evaluator predicates** decide, from the DB alone, whether a goal passed.

---

## 2. Auth flow

```mermaid
sequenceDiagram
  participant C as Agent / probe.py / Bruno
  participant S as AgentSwitch
  C->>S: POST /api/auth/login  { email, password }
  S-->>C: { token }   (the Bearer token)
  C->>S: POST /api/mcp  Authorization: Bearer &lt;token&gt;
  S-->>C: JSON-RPC result
  Note over C,S: A JSON-RPC error still returns HTTP 200 — check the envelope, not just the status.
  Note over C,S: The web UI is different: cookie + X-CSRF-Token header (we don't use that path).
```

The password only ever appears in the login call, sourced from a git-ignored place (`.env` or
a Bruno secret). The token is short-lived and never written to disk.

---

## 3. The graded task, as data flow

Request: **"Publish a post about the new fixture line, and tell me which pages nobody reads."**

```mermaid
flowchart TD
  req["Request (2 goals in one)"]
  req --> A["Half A: publish a post"]
  req --> B["Half B: which pages nobody reads"]

  A --> a1["BlogPost.create (draft about the fixture line)"]
  a1 --> a2["reach published state:<br/>submit_for_review → approve_publish, or publish"]
  a2 --> dbw[("DB: a published post now exists")]

  B --> b1["endpoint.website.conversion_attribution (per page)"]
  b1 --> b2["define 'no traffic' = pages with zero conversions/outcomes<br/>(state the definition; refuse/caveat where unprovable)"]
  b2 --> ans["Answer: the low/zero-engagement pages"]

  dbw --> V["Harness verifier reads the DB"]
  ans --> V
  V --> P["predicates:<br/>web.publish_post · web.pages_without_traffic"]
  P --> score["pass / fail (from DB state, not wording)"]
```

The key design fact lives in Half B: the platform has **no raw page-view counter**, only
conversion data. So "traffic" has to be *defined* by us and defended — and the case where it
cannot be answered truthfully is our built-in **refusal** task.

---

## 4. The harness loop (where the points are)

```mermaid
flowchart LR
  task["Task<br/>(goal + fixed inputs)"] --> run["Run the agent"]
  run --> journal[("Raw run journal<br/>written to disk FIRST")]
  journal --> verify["Verifier reads DB state"]
  verify --> fields["Score: outcome · integrity · verification · cost"]
  fields --> report["Report"]
```

Rules the harness enforces (straight from the grading spec):

- **Verify from the database, never from the agent's prose.**
- **Write the raw run to disk before scoring** — so any score can be recomputed later without
  re-running the model.
- **At least one task whose correct answer is a refusal.**
- **Tests are hand-written** (a test written by Claude/Codex scores zero); 10 points each, plus
  100 points for every new reproducible platform bug.

---

## 5. Code flow (planned module shape)

```
agent/
  mcp_client.py     # login(), call(name, args); holds the Bearer token
  perception.py     # read the slice of state a task needs (Webpage.list, conversion_attribution, ...)
  decision.py       # LLM plans the next step against the goal
  action.py         # execute a tools/call, then re-read (state moves underneath us)
  loop.py           # perceive → decide → act until the predicate is satisfiable
harness/
  tasks/            # one file per task: goal, inputs, the verifier
  verifiers.py      # read DB via the API, return pass/fail + evidence
  run.py            # run a task, journal to disk, then score
  runs/             # git-ignored raw journals
```

This mirrors the 4-layer pipeline the course already taught (Perception → Memory → Decision →
Action); we reuse that shape rather than invent a new one.
