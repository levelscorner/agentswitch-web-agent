"""Config from the environment (see .env.example). Never hardcode secrets here."""
import os

AS_BASE = os.environ.get("AS_BASE", "https://agentswitch.theschoolofai.in").rstrip("/")
AS_EMAIL = os.environ.get("AS_EMAIL", "team09@theschoolofai.in")

# Website IDs discovered during the scrape (safe to keep — not secret).
WEBSITE_SURYODAYA = os.environ.get("AS_WEBSITE_SURYODAYA", "dfca595d-4248-4b07-988f-fcfbd3f3caf1")
WEBSITE_SURYATOOLS = os.environ.get("AS_WEBSITE_SURYATOOLS", "3b417d55-0a29-4bae-86ee-3ce5efbe375d")

# Marker subject for the refusal -> escalation. The agent raises an AgentEscalation with
# this subject (idempotent); the harness verifier reads it back from the DB. Keeping it a
# known constant is the contract between the two — like the website ids above.
REFUSAL_ESCALATION_SUBJECT = os.environ.get(
    "AS_REFUSAL_ESCALATION_SUBJECT",
    "team09 refusal: exact per-page pageviews unavailable")

# An AgentEscalation must reference a session. We attach ours to OUR OWN session (created
# by us, with this marker title) — never another team's — and reuse it across runs.
AGENT_SESSION_TITLE = os.environ.get("AS_AGENT_SESSION_TITLE", "team09 web-agent")

# The password is read at login time from AS_PASSWORD; it is never stored on an object.
