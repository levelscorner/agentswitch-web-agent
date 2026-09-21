"""Hand-written known-bug regression tests. Each asserts the CORRECT behaviour, so it
raises AssertionError while the bug is present, and goes green once staff fix it."""
from agent.client import Client, MCPError
from agent import config

_client = None
def client():
    global _client
    if _client is None:
        _client = Client.login()
    return _client

WID = config.WEBSITE_SURYODAYA


def test_view_count():
    c = client()
    p = c.call("BlogPost.create", {"title": "[TEST]", "slug": "t-vc", "website_id": WID, "content": "x", "view_count": 999})
    pid = p["id"]
    try:
        got = c.call("BlogPost.get", {"id": pid}).get("view_count")
        assert got == 0, f"BUG: view_count stored as {got!r} (should be 0)"
    finally:
        for t in ("BlogPost.unpublish", "BlogPost.archive"):
            try: c.call(t, {"id": pid})
            except MCPError: pass


def test_site_priority():
    c = client()
    p = c.call("Webpage.create", {"title": "[TEST]", "slug": "t-sp", "website_id": WID, "sitemap_priority": 99})
    pid = p["id"]
    try:
        got = c.call("Webpage.get", {"id": pid}).get("sitemap_priority")
        assert 0.0 <= got <= 1.0, f"BUG: sitemap_priority stored as {got!r} (must be 0.0-1.0)"
    finally:
        for t in ("Webpage.unpublish", "Webpage.archive"):
            try: c.call(t, {"id": pid})
            except MCPError: pass


def test_redirect_reject():
    c = client()
    rid = None
    try:
        try:
            r = c.call("WebsiteRedirect.create", {"website_id": WID, "from_path": "/t-loop", "to_path": "/t-loop", "is_active": False})
            rid = r.get("id")
        except MCPError:
            return  # good: the platform rejected it
        g = c.call("WebsiteRedirect.get", {"id": rid})
        assert g.get("from_path") != g.get("to_path"), "BUG: self-redirect (from_path == to_path) was accepted"
    finally:
        if rid:
            try: c.call("WebsiteRedirect.update", {"id": rid, "is_active": False})
            except MCPError: pass


if __name__ == "__main__":
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn(); print(f"PASS {_name}")
            except AssertionError as e:
                print(f"BUG-CAUGHT {_name}: {e}")
            except MCPError as e:
                print(f"BUG-CAUGHT {_name} (MCPError): {e}")
            except Exception as e:
                print(f"BUG-CAUGHT {_name} (Exception): {e}")