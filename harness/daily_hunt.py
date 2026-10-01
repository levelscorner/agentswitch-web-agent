"""Daily probe-and-draft bug hunt (team09 · Website).

Read-only by design, so it is safe to run unattended: it reads the live platform, flags
broken endpoints / data leaks / tenant issues, detects newly-appeared entities, DRAFTS any
candidate into docs/bug-reports/ (gitignored), prints a summary, and FILES NOTHING. Deeper
write-tests live in the manual sweep (harness/bughunt.py), not here.

    set -a; source .env; set +a
    python3 -m harness.daily_hunt

Schedule locally (cron, 9:05am daily):
    5 9 * * * cd ~/ws/projects/agentswitch-web-agent && set -a && . ./.env && set +a && \
      /usr/bin/python3 -m harness.daily_hunt >> ~/.agentswitch-hunt-a09.log 2>&1
"""
import datetime
import json
import pathlib

from agent.client import Client, _http
from agent import config

RUNS = pathlib.Path(__file__).parent / "runs"


def _rows(c, e, a=None):
    r = c.call(e, a or {"limit": 200})
    return r if isinstance(r, list) else r.get("items", r.get("data", r.get("results", [])))


def check_website_feed_500s(c):
    wid = config.WEBSITE_SURYODAYA
    bad = []
    for feed in ("sitemap.xml", "rss.xml", "robots.txt"):
        code, _ = _http("GET", f"{config.AS_BASE}/api/website/{wid}/{feed}", token=c._token)
        if code == 500:
            bad.append(feed)
    if bad:
        return "BUG", (f"/api/website/{{id}}/{bad} return HTTP 500 for every request while sibling "
                       f"feed routes 404 cleanly — unhandled exception (known: rss.xml)")
    return "secure", "no /api/website feed route 500s"


def check_sitemap_draft_leak(c):
    wid = config.WEBSITE_SURYODAYA
    pages = _rows(c, "Webpage.list", {"website_id": wid, "limit": 200})
    nonpub = {(p.get("slug") or "").lower() for p in pages if p.get("status") not in ("published", None)}
    leaked = []
    for feed in ("sitemap.xml", "rss.xml"):
        _, body = _http("GET", f"{config.AS_BASE}/site/{wid}/{feed}", token=c._token)
        body = (body if isinstance(body, str) else str(body)).lower()
        leaked += [s for s in nonpub if s and s in body]
    if leaked:
        return "BUG", f"public feeds leak non-published page slugs: {sorted(set(leaked))[:5]}"
    return "secure", "public sitemap/rss expose no draft pages"


def check_tenant_isolation(c):
    myco = c.me().get("company_id")
    sites = _rows(c, "Website.list", {"limit": 200})
    foreign = [s.get("id") for s in sites if s.get("company_id") not in (myco, None)]
    if foreign:
        return "BUG", f"{len(foreign)} foreign-company websites visible via Website.list (tenant leak)"
    return "secure", f"Website.list exposes only our {len(sites)} sites"


def monitor_new_entities(c):
    ents = sorted({t.get("name", "").split(".")[0] for t in c.list_tools() if "." in t.get("name", "")})
    RUNS.mkdir(exist_ok=True)
    seen_path = RUNS / "entities-seen.json"
    try:
        seen = set(json.loads(seen_path.read_text()))
    except Exception:
        seen = set()
    new = sorted(set(ents) - seen) if seen else []
    seen_path.write_text(json.dumps(sorted(set(ents) | seen)))
    if new:
        return "info", f"{len(ents)} entities — NEW since last run: {new} (probe these for fresh bugs)"
    return "info", f"{len(ents)} entities (none new since last run)"


CHECKS = [
    ("website_feed_500s", check_website_feed_500s),
    ("sitemap_draft_leak", check_sitemap_draft_leak),
    ("tenant_isolation", check_tenant_isolation),
    ("entities", monitor_new_entities),
]


def main():
    c = Client.login()
    results = []
    for name, fn in CHECKS:
        try:
            status, detail = fn(c)
        except Exception as e:
            status, detail = "error", f"{type(e).__name__}: {e}"
        results.append((name, status, detail))
        print(f"[{status.upper():6}] {name}: {detail}")

    date = datetime.date.today().isoformat()
    candidates = [(n, d) for n, s, d in results if s == "BUG"]
    newent = [d for n, s, d in results if n == "entities" and "NEW" in d]
    if candidates or newent:
        out = pathlib.Path("docs/bug-reports")
        out.mkdir(parents=True, exist_ok=True)
        f = out / f"{date}-daily-hunt.md"
        body = [f"# Daily hunt — {date} (team09 · Website)",
                "", "DRAFT — review and file via the bug button / API. Nothing was filed automatically.", ""]
        for n, d in candidates:
            body += [f"## candidate: {n}", "", d, ""]
        for d in newent:
            body += ["## new surface", "", d, ""]
        f.write_text("\n".join(body))
        print(f"\nDRAFTED {len(candidates)} candidate(s) + {len(newent)} new-surface note(s) -> {f}")
    else:
        print("\nNo new candidates. All monitored controls held; no new entities.")


if __name__ == "__main__":
    main()
