"""Internal regression tests for harness verifier logic.

Claude-authored dev tests — NOT the graded 10-pt hand-tests (those are yours).
Pure functions only: no login, no network. They pin the orphan-detection rule so
the DB-truth verifier can't silently share the agent's buggy substring heuristic.

Run:
    python3 -m harness.test_verifiers_internal
    # or: pytest harness/test_verifiers_internal.py
"""
from harness.verifiers import _orphans, _tenant_clean, trace_recorded, _count_published_fixtures
from harness.four_fields import verification_of


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


# --- Phase 2: real four-field scoring ---------------------------------------

def test_tenant_clean_true_when_only_our_sites_visible():
    assert _tenant_clean([{"id": "A"}, {"id": "B"}], {"A", "B"}) is True


def test_tenant_clean_false_when_a_foreign_site_is_visible():
    assert _tenant_clean([{"id": "A"}, {"id": "FOREIGN"}], {"A", "B"}) is False


def test_verification_na_when_agent_did_not_run():
    assert verification_of(ran=False, state={}, reread_key="published_status") == "n/a"


def test_verification_verified_when_reread_field_present():
    assert verification_of(ran=True, state={"published_status": "published"},
                           reread_key="published_status") == "verified"


def test_verification_no_attempt_when_reread_field_absent():
    assert verification_of(ran=True, state={}, reread_key="published_status") == "no_attempt"


# --- Phase 3: observability trace --------------------------------------------

def test_trace_recorded_true_with_timings_and_order():
    assert trace_recorded({"timings": {"fetch_pages": 0.12}, "dag_order": ["fetch_pages"]}) is True


def test_trace_recorded_false_when_empty():
    assert trace_recorded({}) is False


def test_trace_recorded_false_without_dag_order():
    assert trace_recorded({"timings": {"fetch_pages": 0.12}}) is False


# --- Phase 4: idempotency coverage -------------------------------------------

def test_count_published_fixtures_only_counts_published_fixture_posts():
    posts = [{"status": "published", "title": "Our new fixture line"},
             {"status": "draft", "title": "fixture draft"},
             {"status": "published", "title": "About us"}]
    assert _count_published_fixtures(posts) == 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok:", fn.__name__)
    print(f"\n{len(fns)} passed")
