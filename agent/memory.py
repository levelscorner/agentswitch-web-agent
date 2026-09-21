"""3-tier memory (S07) — a small SKELETON for now, real system later.

Three tiers, three simple ideas:
  - Factual    : facts we know          e.g. "publish tool = BlogPost.publish"   -> facts.json
  - Episodic   : a diary of past runs   e.g. "last run: created+published post X" -> episodes.json
  - Preference : standing rules         e.g. house style, our "no-traffic" meaning -> prefs.json

Today these are plain JSON files (dead simple, and enough for Week 1-2).
LATER (TODO): back Factual/Episodic onto the platform's own tables so memory lives
on the server and survives everywhere:
  - AgentMemory  -> facts
  - AgentSkill   -> reusable recipes (episodic/procedural)
  - AgentMessage -> notes between our agents
and add semantic search (embeddings) for retrieval when we have many entries.
"""
import json
import time
from pathlib import Path

MEM_DIR = Path(__file__).parent / "mem_store"


class _JsonStore:
    def __init__(self, name):
        self.path = MEM_DIR / f"{name}.json"

    def _load(self):
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {}

    def _save(self, data):
        MEM_DIR.mkdir(exist_ok=True)
        self.path.write_text(json.dumps(data, indent=2))


class KeyValueTier(_JsonStore):
    """Factual and Preference are both simple key -> value stores."""

    def get(self, key, default=None):
        return self._load().get(key, default)

    def set(self, key, value):
        data = self._load()
        data[key] = value
        self._save(data)

    def all(self):
        return self._load()


class EpisodicTier(_JsonStore):
    """A growing list of past runs (a diary)."""

    def add(self, episode: dict):
        data = self._load()
        data.setdefault("episodes", []).append({**episode, "at": time.time()})
        self._save(data)

    def recent(self, n=5):
        return self._load().get("episodes", [])[-n:]


class Memory:
    """One object the agent carries. Read at the start of a task, write at the end."""

    def __init__(self):
        self.facts = KeyValueTier("facts")        # -> TODO AgentMemory
        self.episodes = EpisodicTier("episodes")  # -> TODO AgentSkill
        self.prefs = KeyValueTier("prefs")        # standing rules

    def seed_defaults(self):
        """Give the agent its starting preferences so it is useful on day one."""
        if not self.prefs.get("house_style"):
            self.prefs.set("house_style",
                           "Clear, terse, benefit-led. Short sentences. No hype.")
        if not self.prefs.get("no_traffic_definition"):
            self.prefs.set("no_traffic_definition",
                           "orphan pages: published, not in any WebsiteMenu, "
                           "not linked from another page")
        return self


if __name__ == "__main__":
    m = Memory().seed_defaults()
    print("prefs:", m.prefs.all())
    print("recent episodes:", m.episodes.recent())
