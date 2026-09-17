"""Config from the environment (see .env.example). Never hardcode secrets here."""
import os

AS_BASE = os.environ.get("AS_BASE", "https://agentswitch.theschoolofai.in").rstrip("/")
AS_EMAIL = os.environ.get("AS_EMAIL", "team09@theschoolofai.in")

# Website IDs discovered during the scrape (safe to keep — not secret).
WEBSITE_SURYODAYA = os.environ.get("AS_WEBSITE_SURYODAYA", "dfca595d-4248-4b07-988f-fcfbd3f3caf1")
WEBSITE_SURYATOOLS = os.environ.get("AS_WEBSITE_SURYATOOLS", "3b417d55-0a29-4bae-86ee-3ce5efbe375d")

# The password is read at login time from AS_PASSWORD; it is never stored on an object.
