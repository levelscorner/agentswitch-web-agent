"""LLM wrapper for drafting content (Anthropic SDK).

Default model claude-opus-5; override with AGENT_MODEL (e.g. claude-haiku-4-5 to route
cheap drafts, S15-style). Reads ANTHROPIC_API_KEY from the environment (.env).
"""
import os

import anthropic

MODEL = os.environ.get("AGENT_MODEL", "claude-opus-5")
_client = None


def _get():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def draft(system, prompt, max_tokens=4000):
    """Return (text, usage). Non-streaming; fine for short posts."""
    resp = _get().messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    usage = {"model": MODEL, "in": resp.usage.input_tokens, "out": resp.usage.output_tokens}
    return text, usage
