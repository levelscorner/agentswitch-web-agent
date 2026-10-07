"""Internal regression tests for harness verifier logic.

Claude-authored dev tests — NOT the graded 10-pt hand-tests (those are yours).
Pure functions only: no login, no network. They pin the orphan-detection rule so
the DB-truth verifier can't silently share the agent's buggy substring heuristic.

Run:
    python3 -m harness.test_verifiers_internal
    # or: pytest harness/test_verifiers_internal.py
"""
from harness.verifiers import _orphans


def _page(pid, slug, status="published"):
    return {"id": pid, "slug": slug, "status": status}


def test_page_linked_only_by_page_id_is_not_orphan():
    # slug 'about' appears in no menu url, but a menu item targets it by page_id.
    # The old str(menus) substring heuristic flags it as an orphan (false positive).
    pages = [_page("p1", "about")]
    menus = [{"page_id": "p1", "url": None, "label": "Home"}]
    assert _orphans(pages, menus) == []


def test_slug_appearing_coincidentally_in_text_is_still_orphan():
    # 'news' is a substring of 'newsletter' and 'News archive', so the blob heuristic
    # treats the page as linked (false negative). Structurally it is an orphan.
    pages = [_page("p2", "news")]
    menus = [{"page_id": None, "url": "https://example.com/newsletter", "label": "News archive"}]
    got = {p["id"] for p in _orphans(pages, menus)}
    assert got == {"p2"}


def test_page_linked_by_matching_url_path_is_not_orphan():
    pages = [_page("p3", "contact")]
    menus = [{"page_id": None, "url": "https://suryodaya.example/contact"}]
    assert _orphans(pages, menus) == []


def test_draft_pages_are_never_orphans():
    pages = [_page("d1", "secret", status="draft")]
    assert _orphans(pages, []) == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok:", fn.__name__)
    print(f"\n{len(fns)} passed")
