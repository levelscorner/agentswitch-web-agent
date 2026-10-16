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
from agent.verify import _orphans_from
from agent.subgraphs import _outcome_summary, _caveat_from


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


# --- Agent self-check: verify.py uses the SAME structural rule, not str(menus) -----

def test_agent_verify_orphans_structural_matches_grader():
    # The agent's own S17 reality-check must use structural reachability, not the old
    # str(menus).lower() substring test: a page linked only by page_id is NOT an orphan,
    # and a slug that is a coincidental substring of menu text IS still an orphan.
    pages = [_page("p1", "about"), _page("p2", "news")]
    menus = [{"page_id": "p1", "url": None},
             {"page_id": None, "url": "https://example.com/newsletter"}]
    got = {p["id"] for p in _orphans_from(pages, menus)}
    assert got == {"p2"}  # p1 linked by page_id; p2's slug only coincides inside 'newsletter'


def test_agent_verify_orphans_ignores_drafts():
    assert _orphans_from([_page("d1", "secret", status="draft")], []) == []


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


def test_verification_verified_when_reread_present_and_confirmed():
    assert verification_of(ran=True, state={"published_status": "published"},
                           reread_key="published_status", confirmed=True) == "verified"


def test_verification_unverified_when_reread_present_but_not_confirmed():
    # #5 fallback left the post as a draft: the agent DID re-read, but it did not land.
    assert verification_of(ran=True, state={"published_status": "draft"},
                           reread_key="published_status", confirmed=False) == "unverified"


# --- #3: conversion_attribution probe makes the caveat evidence-based -------------

def test_outcome_summary_reads_coverage_and_attributed_conversions():
    result = {"paths": [{}, {}, {}], "summary": {"conversions_attributed": 0}}
    assert _outcome_summary(result) == {"covered": 3, "with_outcomes": 0}
    result2 = {"paths": [{}, {}], "summary": {"conversions_attributed": 2}}
    assert _outcome_summary(result2) == {"covered": 2, "with_outcomes": 2}


def test_caveat_unavailable_falls_back_to_structural_proxy():
    from agent.subgraphs import CAVEAT
    assert _caveat_from(None) == CAVEAT


def test_caveat_reports_zero_outcomes_with_real_count():
    c = _caveat_from({"covered": 8, "with_outcomes": 0})
    assert "0 attributed conversions across 8" in c


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
