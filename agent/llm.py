"""LLM wrapper with model routing (S15) + reliability (S12), provider-agnostic.

Two providers, chosen by environment at import time:
  - OpenAI-compatible  — when OPENAI_API_KEY is set (the AgentSwitch official run
    supplies OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL). Anthropic/Gemini SDKs
    do not work there, so we speak OpenAI.
  - Anthropic          — otherwise (local dev with our own ANTHROPIC_API_KEY).

Same public API either way: draft() / draft_json(). Model routing: cheap tier for
simple work (plan, draft), strong tier for hard judgment (verify). On the OpenAI path
both tiers collapse to the single OPENAI_MODEL the server provides.

Reliability: transient API errors retry with backoff; a per-run Breaker (set via
set_breaker) caps total calls and opens after repeated failures.
"""
import os

from agent import reliability

PROVIDER = "openai" if os.environ.get("OPENAI_API_KEY") else "anthropic"

if PROVIDER == "openai":
    try:
        import openai  # in requirements; installed on the server (install step has internet)
    except ImportError:
        PROVIDER = "anthropic"   # key set but SDK absent (local dev) — fall back to Claude

if PROVIDER == "openai":
    _OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    _TRANSIENT = tuple(
        getattr(openai, n) for n in
        ("APIConnectionError", "APITimeoutError", "RateLimitError", "InternalServerError")
        if hasattr(openai, n)
    ) or (Exception,)
else:
    import anthropic
    MODELS = {
        "simple": os.environ.get("MODEL_SIMPLE", "claude-haiku-4-5"),
        "hard": os.environ.get("MODEL_HARD", "claude-opus-5"),
    }
    _OVERRIDE = os.environ.get("AGENT_MODEL")  # pins both tiers when set
    _TRANSIENT = tuple(
        getattr(anthropic, n) for n in
        ("APIConnectionError", "APITimeoutError", "RateLimitError", "InternalServerError")
        if hasattr(anthropic, n)
    ) or (Exception,)

_client = None
_BREAKER = None  # per-run guard; set by respond.respond()


def _get():
    global _client
    if _client is None:
        if PROVIDER == "openai":
            _client = openai.OpenAI()          # reads OPENAI_BASE_URL + OPENAI_API_KEY
        else:
            _client = anthropic.Anthropic()
    return _client


def set_breaker(b):
    """Install the per-run budget/circuit breaker (or None to disable)."""
    global _BREAKER
    _BREAKER = b


def _model(tier):
    if PROVIDER == "openai":
        return _OPENAI_MODEL
    return _OVERRIDE or MODELS.get(tier, MODELS["hard"])


def draft(system, prompt, tier="simple", max_tokens=4000):
    """Return (text, usage). Routes by tier, retries transient API errors with
    backoff, and counts against the run breaker."""
    model = _model(tier)

    if PROVIDER == "openai":
        def call():
            return _get().chat.completions.create(
                model=model, max_tokens=max_tokens,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": prompt}],
            )
        resp = reliability.call_with_retries(call, transient=_TRANSIENT, breaker=_BREAKER)
        text = resp.choices[0].message.content or ""
        u = getattr(resp, "usage", None)
        usage = {"model": model,
                 "in": getattr(u, "prompt_tokens", 0) if u else 0,
                 "out": getattr(u, "completion_tokens", 0) if u else 0}
        return text, usage

    def call():
        return _get().messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": prompt}],
        )
    resp = reliability.call_with_retries(call, transient=_TRANSIENT, breaker=_BREAKER)
    text = "".join(b.text for b in resp.content if b.type == "text")
    usage = {"model": model, "in": resp.usage.input_tokens, "out": resp.usage.output_tokens}
    return text, usage


def draft_json(system, prompt, tier="simple", max_tokens=800):
    """Draft and parse JSON. On invalid JSON, ask the model once to repair it."""
    text, _ = draft(system, prompt, tier=tier, max_tokens=max_tokens)
    try:
        return reliability.extract_json(text)
    except Exception:
        fixed, _ = draft("Return ONLY valid JSON, no prose.",
                         "Fix this into valid JSON:\n" + text, tier="simple", max_tokens=max_tokens)
        return reliability.extract_json(fixed)
