"""Write-path bug hunter — where the 100-pt bugs actually hide.

Read-only invariants already checked out clean. Real bugs are usually "the call
returned success but the database did not change" (the brief's own WorkOrder example).
This exercises our seat's write paths with before/after DB reads and flags any mismatch.

SAFE BY DEFAULT: with no flag it only DUMPS the create-schemas and explains — no writes.
Pass --run to actually create a clearly-marked test post, check the invariants, and
clean it up afterwards. Every test row is titled "[HARNESS TEST] ..." so it is obvious.

    set -a; source .env; set +a
    python3 -m harness.bughunt            # dry: schema + plan only
    python3 -m harness.bughunt --run      # live: create/publish/cleanup + report bugs
"""
import sys
import time

from agent import config
from agent.client import Client, MCPError

TEST_TITLE = "[HARNESS TEST] fixture line — delete me"


def _schema(client, tool):
    for t in client.list_tools():
        if t.get("name") == tool:
            s = t.get("inputSchema") or t.get("input_schema") or {}
            return {"required": s.get("required", []), "props": list((s.get("properties") or {}).keys())}
    return None


def _get(client, tool, _id):
    try:
        return client.call(tool, {"id": _id})
    except MCPError as e:
        return {"_error": str(e)}


def dry(client):
    print("BlogPost.create schema:", _schema(client, "BlogPost.create"))
    print("Webpage.create  schema:", _schema(client, "Webpage.create"))
    print("\nWith --run this will: create a draft -> read back (did it persist?) ->")
    print("publish -> read back (did status flip to 'published'?) -> archive to clean up,")
    print("flagging any 'success but no DB change' as a BUG candidate.")


def hunt(client):
    bugs = []
    # Build a real, valid payload (bad input would look like a bug but isn't).
    payload = {
        "title": TEST_TITLE,
        "slug": f"harness-test-fixture-{int(time.time())}",
        "website_id": config.WEBSITE_SURYODAYA,
        "content": "Harness write-path test. Safe to delete.",
    }
    for f in (_schema(client, "BlogPost.create") or {}).get("required", []):
        payload.setdefault(f, "test")

    created = None
    try:
        created = client.call("BlogPost.create", payload)
        pid = created.get("id") if isinstance(created, dict) else None
        print(f"created id={pid}")

        # INVARIANT 1: create returned success -> the row exists and is a draft
        back = _get(client, "BlogPost.get", pid)
        if not isinstance(back, dict) or back.get("id") != pid:
            bugs.append(f"BlogPost.create returned an id but BlogPost.get({pid}) did not return it: {back}")
        elif back.get("status") not in (None, "draft"):
            bugs.append(f"new BlogPost is not a draft; status={back.get('status')!r}")

        # INVARIANT 2: publish -> status flips to 'published' in the DB
        try:
            client.call("BlogPost.publish", {"id": pid})
        except MCPError as e:
            bugs.append(f"BlogPost.publish raised: {e}")
        back2 = _get(client, "BlogPost.get", pid)
        if isinstance(back2, dict) and back2.get("status") != "published":
            bugs.append(f"BlogPost.publish returned success but status stayed {back2.get('status')!r} "
                        f"(post id={pid}) — a silent no-op.")
        else:
            print(f"publish OK, status={back2.get('status') if isinstance(back2, dict) else back2!r}")

    finally:
        # CLEAN UP: unpublish + archive the test post so we do not pollute the site.
        if created and isinstance(created, dict) and created.get("id"):
            pid = created["id"]
            for tool in ("BlogPost.unpublish", "BlogPost.archive"):
                try:
                    client.call(tool, {"id": pid})
                except MCPError:
                    pass
            print(f"cleaned up test post id={pid}")

    return bugs


def hunt_transitions(client):
    """Edge cases in the workflow state machine, where silent bugs live."""
    bugs = []
    wid = config.WEBSITE_SURYODAYA
    ids = []

    def mk(slug):
        p = client.call("BlogPost.create",
                        {"title": TEST_TITLE, "slug": slug, "website_id": wid, "content": "x"})
        if isinstance(p, dict) and p.get("id"):
            ids.append(p["id"])
        return p

    try:
        base = f"harness-tx-{int(time.time())}"

        # A) duplicate slug — a real bug ONLY if the second slug equals the first
        #    (the platform auto-uniquifies with a -2 suffix, which is correct).
        a = mk(base); b = mk(base)
        sa = _get(client, "BlogPost.get", a.get("id")).get("slug")
        sb = _get(client, "BlogPost.get", b.get("id")).get("slug")
        if sa == sb:
            bugs.append(f"duplicate slug accepted — two posts share slug {sa!r}")
        else:
            print(f"dup-slug: auto-uniquified {sa!r} -> {sb!r} (good)")

        # D) integrity — the analytics view_count must NOT be settable by the client
        inj = client.call("BlogPost.create", {"title": TEST_TITLE, "slug": base + "-inj",
                          "website_id": wid, "content": "x", "view_count": 424242})
        if isinstance(inj, dict) and inj.get("id"):
            ids.append(inj["id"])
            stored = _get(client, "BlogPost.get", inj["id"]).get("view_count")
            if stored in (424242, 424242.0):
                bugs.append(f"BlogPost.view_count is client-settable on create (stored {stored!r}) "
                            f"- lets a user fabricate analytics")
            else:
                print(f"view_count injection ignored (stored {stored!r}) (good)")

        # B) illegal transition — approve_publish a draft that was NEVER submitted
        c = mk(base + "-c"); cid = c.get("id")
        try:
            client.call("BlogPost.approve_publish", {"id": cid})
            st = _get(client, "BlogPost.get", cid).get("status")
            if st == "published":
                bugs.append(f"approve_publish PUBLISHED a draft never submitted_for_review "
                            f"(id={cid}) — a workflow bypass")
            else:
                print(f"illegal approve: status stayed {st!r}")
        except MCPError:
            print("illegal approve: rejected (good)")

        # C) observe the normal workflow; flag only a success-with-no-change
        d = mk(base + "-d"); did = d.get("id")
        for tool in ("BlogPost.submit_for_review", "BlogPost.approve_publish"):
            before = _get(client, "BlogPost.get", did).get("status")
            try:
                client.call(tool, {"id": did})
            except MCPError as e:
                print(f"{tool}: raised {e}")
                continue
            after = _get(client, "BlogPost.get", did).get("status")
            print(f"{tool}: {before!r} -> {after!r}")
            if after == before:
                bugs.append(f"{tool} returned success but status stayed {after!r} (id={did}) — silent no-op")
    finally:
        for i in ids:
            for tool in ("BlogPost.unpublish", "BlogPost.archive"):
                try:
                    client.call(tool, {"id": i})
                except MCPError:
                    pass
        print(f"cleaned up {len(ids)} test posts")
    return bugs


def main():
    client = Client.login()
    if "--run" not in sys.argv:
        dry(client)
        return
    bugs = hunt(client) + hunt_transitions(client)
    print("\n=== BUG CANDIDATES ===")
    if not bugs:
        print("none — write paths behaved correctly.")
    for b in bugs:
        print(" -", b)


if __name__ == "__main__":
    main()
