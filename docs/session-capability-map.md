# Session → capability map

The capstone is where the whole course lands in one agent. This maps each session to what our
**Website agent** should take from it, and how much it matters for *our two goals*.

Priority: **★ backbone** (build on it) · **● supporting** (fold in) · **○ optional / skip**.

| S | What it taught | What our Website agent takes | Pri |
|---|---|---|---|
| S01 | Chrome extension calling an LLM API | just the primitive: call an LLM | ○ |
| S02 | Streaming, Gemini Flash / Claude Haiku | cheap-model + streaming (feeds S15 routing) | ○ |
| S03 | Full-stack agent: take a goal, run ≥1 tool, return result | **the core skeleton** — request in → tool calls → result | ★ |
| S04 | Build an MCP **server** over a real API | we are the MCP **client** of `$AS/api/mcp`; deep protocol grip (handshake, `tools/call`, the HTTP-200 error trap) | ★ |
| S05 | Decompose a goal, plan tool use, self-validate | **planner** — split "publish + dead pages" into steps, order the tool calls, self-check | ★ |
| S06 | 4-module **Perception → Memory → Decision → Action**, strategy selection, adaptive retry | **the agent architecture** — our loop, Pydantic-typed | ★ |
| S07 | **3-tier memory** (REMME / Episodic / Factual), persists across sessions | factual (schemas + site map), episodic (the publish "recipe"), prefs (house style, our "no-traffic" definition). Persist in `AgentMemory` / `AgentSkill` (private to us) | ★ |
| S08 | Multi-agent **DAG**, 3+ agent types, parallel, resumable | **orchestration** — run the two goals as a DAG (publisher · analyst · verifier), blackboard shared state, resumable | ★ |
| S09 | Web research across 5+ sources → synthesis | already used it for the gap report; reuse to research real fixture-line content for the post | ● |
| S10 | Desktop agent via vision + a11y tree | least relevant (we drive an API); at most, verify the published page renders | ○ |
| S11 | **Channel adapter** (ingress + reply routing) | **email channel** — the brief mandates agent↔agent over email; our escalation + answer channel | ● |
| S12 | Container isolation + **circuit breaker** | **safety** — circuit breaker on API failures, JSON-repair on LLM output, never write outside our seat, clean refusal | ★ |
| S13 | **A2A** — Agent Card, delegate to ≥2 agents | cross-app data via an EA / other team's agent; publish our own Agent Card; delegate | ● |
| S14 | Dynamic **interactive UI** (A2UI / AG-UI) | render the dead-pages answer as an interactive report (human-facing; grading is DB state) | ○ |
| S15 | **Model router** + cost dashboard | route: cheap model to *draft*, strong model to *decide*; track cost (S18's Cost field) | ● |
| S16 | Event-driven agent, ≥1 hr autonomous, audit log | optional continuous mode; our audit = platform audit trail + run journals | ○ |
| S17 | **Coding agent**: draft → verify → refine, System 2, `SKILL.md`, "can't mark its own homework" | **the verify-refine loop** + the rule that the agent must **not self-certify** — verifiers read the DB; plus bug-finding | ★ |
| S18 | **Eval harness**: 20+ tests, scoring, regression, compare 2 configs, four-field score | **THE HARNESS** — our scorer (Outcome / Integrity / Verification / Cost), journal-to-disk first | ★ |
| S19 | Finalize plan (GitHub Projects) / PR to Arcturus | the repo + this plan (done) | ✓ |

**The best combination (our backbone):** S03 skeleton → S06 architecture → S04 MCP client →
S05 planner → S07 memory → S08 DAG orchestration → S12 safety/refusal → S17 verify-refine →
S18 harness. S09 (research), S11 (email), S13 (A2A escalation), S15 (routing) fold in as
supporting layers. S01–02, S10, S14, S16 are skip/optional for *our* two goals.
