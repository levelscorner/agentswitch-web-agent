#!/usr/bin/env python3
"""
Read-only connection test + capability dump for the AgentSwitch Website seat.

Logs in, confirms our seat, and dumps the two things we most need for week 1:
  1. our MCP tool catalogue  (tools/list)  = what our agent is allowed to do
  2. the entity schemas       (/api/schemas) = the shape of the data behind it

Creates / changes NOTHING on the platform. Never prints or stores the token.
Reads config from the environment (see .env.example):
  AS_BASE, AS_EMAIL, AS_PASSWORD

    cp .env.example .env && edit it
    set -a; source .env; set +a
    python3 probe.py
"""
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

BASE = os.environ.get("AS_BASE", "https://agentswitch.theschoolofai.in").rstrip("/")
EMAIL = os.environ.get("AS_EMAIL", "")
PASSWORD = os.environ.get("AS_PASSWORD", "")
OUT = Path(__file__).parent / "probe-out"
WEBSITE_HINTS = ("page", "post", "blog", "publication", "article", "view", "visit", "analytic")


def _req(method, path, token=None, body=None, timeout=30):
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, None


def login():
    if not EMAIL or not PASSWORD:
        sys.exit("Set AS_EMAIL and AS_PASSWORD in the environment (see .env.example).")
    status, body = _req("POST", "/api/auth/login",
                        body={"email": EMAIL, "password": PASSWORD})
    if status != 200 or not isinstance(body, dict):
        sys.exit(f"Login failed (HTTP {status}). Check AS_BASE / email / password.")
    token = body.get("token") or body.get("access_token") or body.get("jwt")
    if not token:
        sys.exit(f"Logged in but no token field found. Response keys: {list(body)}")
    return token


def mcp(token, method, params):
    """One JSON-RPC call. Remember: a JSON-RPC error still returns HTTP 200."""
    status, body = _req("POST", "/api/mcp", token=token,
                        body={"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    err = body.get("error") if isinstance(body, dict) else None
    return status, body, err


def main():
    OUT.mkdir(exist_ok=True)
    token = login()
    print(f"[ok] logged in to {BASE}")

    # 1. Who are we? (the seat, stated by the server)
    _, me = _req("GET", "/api/auth/me", token=token)
    (OUT / "auth_me.json").write_text(json.dumps(me, indent=2))
    if isinstance(me, dict):
        print(f"[seat] email={me.get('email')}  roles={me.get('roles')}")
        print(f"[seat] allowed_apps={me.get('allowed_apps')}")

    # 2. MCP handshake + our tool catalogue = our capability list
    _, init, init_err = mcp(token, "initialize", {
        "protocolVersion": "2025-11-25", "capabilities": {},
        "clientInfo": {"name": "team09-probe", "version": "0.1"}})
    print(f"[mcp] initialize error={init_err}")
    _, tools_resp, tools_err = mcp(token, "tools/list", {})
    tools = (tools_resp or {}).get("result", {}).get("tools", []) if not tools_err else []
    (OUT / "tools_list.json").write_text(json.dumps(tools_resp, indent=2))
    names = sorted(t.get("name", "") for t in tools)
    print(f"[mcp] tools visible to our seat: {len(names)}")
    website = [n for n in names if any(h in n.lower() for h in WEBSITE_HINTS)]
    print(f"[mcp] likely website tools ({len(website)}):")
    for n in website:
        print("        " + n)

    # 3. Entity schemas (the whole business); flag the ones that look like ours
    _, schemas = _req("GET", "/api/schemas", token=token)
    (OUT / "schemas.json").write_text(json.dumps(schemas, indent=2))
    entity_names = list(schemas.keys()) if isinstance(schemas, dict) else []
    print(f"[schemas] total entity types: {len(entity_names)}")
    ours = [e for e in entity_names if any(h in e.lower() for h in WEBSITE_HINTS)]
    print(f"[schemas] website-looking entities ({len(ours)}): {ours}")

    print(f"\nRaw responses saved under {OUT}/ (git-ignored). Token never stored.")


if __name__ == "__main__":
    main()
