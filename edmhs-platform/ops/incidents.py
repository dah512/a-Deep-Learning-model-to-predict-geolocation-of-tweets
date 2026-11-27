"""Turn the daily report into engineering tasks: open a GitHub issue for each site that is DOWN or
DEGRADED (one open issue per site, labeled `site-incident` and its severity), comment on it while it
persists, and close it with a recovery note when the site is UP again.

usage: GITHUB_TOKEN=... GITHUB_REPOSITORY=owner/repo python ops/incidents.py ops/reports/daily/YYYY-MM-DD.json
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

API = "https://api.github.com"
LABEL = "site-incident"


def gh(method: str, path: str, body: dict | None = None):
    req = urllib.request.Request(f"{API}{path}", method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
                                          "Accept": "application/vnd.github+json", "User-Agent": "edmhs-incidents"})
    with urllib.request.urlopen(req, timeout=30) as r:
        txt = r.read()
        return json.loads(txt) if txt else None


def title_for(site_id: str) -> str:
    return f"[site] {site_id} is not healthy"


def sync(report: dict, repo: str, call=gh) -> dict:
    open_issues = {i["title"]: i for i in call("GET", f"/repos/{repo}/issues?labels={LABEL}&state=open&per_page=100") or []}
    actions = {"opened": [], "updated": [], "closed": []}
    for r in report["results"]:
        t = title_for(r["id"])
        bad = r["verdict"] in ("DOWN", "DEGRADED")
        detail = "\n".join(f"- {p['detail']}" for p in r["problems"] if p["kind"] != "info") or "- (no detail)"
        line = f"**{report['date']}: {r['verdict']} ({r['severity']})** {r['url']}\n{detail}"
        if bad and t not in open_issues:
            call("POST", f"/repos/{repo}/issues", {"title": t, "labels": [LABEL, r["severity"].lower()],
                 "body": f"Opened by the daily site review (docs/ops/site_engineering_protocol.md).\n\n{line}"})
            actions["opened"].append(r["id"])
        elif bad:
            call("POST", f"/repos/{repo}/issues/{open_issues[t]['number']}/comments", {"body": line})
            actions["updated"].append(r["id"])
        elif t in open_issues and r["verdict"] == "UP":
            n = open_issues[t]["number"]
            call("POST", f"/repos/{repo}/issues/{n}/comments", {"body": f"**{report['date']}: recovered (UP).** Closing."})
            call("PATCH", f"/repos/{repo}/issues/{n}", {"state": "closed", "state_reason": "completed"})
            actions["closed"].append(r["id"])
    return actions


if __name__ == "__main__":
    rep = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(sync(rep, os.environ["GITHUB_REPOSITORY"])))
