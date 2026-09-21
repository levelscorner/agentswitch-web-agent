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
    sch = _schema(client, "BlogPost.create") or {"required": [], "props": []}
    # Build a minimal valid payload: title + any other required fields (best-effort defaults).
    payload = {"title": TEST_TITLE}
    for f in sch["required"]:
        if f in payload:
            continue
        payload[f] = "harness placeholder" if "content" in f or "body" in f or "slug" in f else "test"

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

    print("\n=== BUG CANDIDATES ===")
    if not bugs:
        print("none — write paths behaved correctly.")
    for b in bugs:
        print(" -", b)
    return bugs


def main():
    client = Client.login()
    if "--run" in sys.argv:
        hunt(client)
    else:
        dry(client)


if __name__ == "__main__":
    main()
