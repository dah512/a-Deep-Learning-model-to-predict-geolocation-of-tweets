"""Weekly aggregate: site availability from the last 7 daily reports + engineering tasks opened/closed.

usage: python ops/weekly.py [--daily ops/reports/daily] [--out ops/reports/weekly] [--end YYYY-MM-DD]

Engineering tasks are GitHub issues and pull requests in `task_repos` (ops/sites.yaml), read with the
GitHub REST API. Set GITHUB_TOKEN to a token with read access to those repositories; without one,
the task section is marked "not collected" rather than reported as zero.
"""
from __future__ import annotations

import argparse
import json
import os
import urllib.request
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from statistics import median

import yaml

API = "https://api.github.com"


def load_days(daily: Path, end: date) -> list[dict]:
    days = []
    for i in range(6, -1, -1):
        f = daily / f"{(end - timedelta(days=i)).isoformat()}.json"
        if f.exists():
            days.append(json.loads(f.read_text()))
    return days


def site_summary(days: list[dict]) -> list[dict]:
    by: dict[str, dict] = defaultdict(lambda: {"verdicts": [], "ms": [], "problems": [], "cert": None})
    for d in days:
        for r in d["results"]:
            s = by[r["id"]]
            s.update(name=r["name"], url=r["url"], critical=r["critical"], status_cfg=r["status_cfg"])
            s["verdicts"].append((d["date"], r["verdict"]))
            if r["checks"].get("response_ms") is not None and r["checks"].get("http_status"):
                s["ms"].append(r["checks"]["response_ms"])
            s["problems"] += [f"{d['date']}: {p['detail']}" for p in r["problems"] if p["kind"] != "info"]
            if r["checks"].get("cert_days_left") is not None:
                s["cert"] = r["checks"]["cert_days_left"]
    out = []
    for sid, s in by.items():
        n = len(s["verdicts"])
        up = sum(v == "UP" for _, v in s["verdicts"])
        out.append({"id": sid, "name": s["name"], "url": s["url"], "critical": s["critical"], "status_cfg": s["status_cfg"],
                    "days": n, "up_days": up, "availability": round(100 * up / n, 1) if n else None,
                    "median_ms": round(median(s["ms"])) if s["ms"] else None, "cert_days_left": s["cert"],
                    "latest": s["verdicts"][-1][1] if s["verdicts"] else None,
                    "trend": "".join({"UP": "▮", "DEGRADED": "▯", "DOWN": "×", "PLANNED": "·"}[v] for _, v in s["verdicts"]),
                    "problems": s["problems"][-5:]})
    return sorted(out, key=lambda x: (x["status_cfg"] != "live", x["availability"] if x["availability"] is not None else 101, x["id"]))


def _gh(path: str, token: str) -> list[dict]:
    items, url = [], f"{API}{path}"
    while url:
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                                                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "edmhs-weekly"})
        with urllib.request.urlopen(req, timeout=30) as r:
            items += json.load(r).get("items", [])
            link = r.headers.get("Link", "")
        url = next((p.split(";")[0].strip("<> ") for p in link.split(",") if 'rel="next"' in p), None)
    return items


def collect_tasks(repos: list[str], start: date, end: date, token: str | None) -> dict | None:
    if not token or not repos:
        return None
    rng = f"{start.isoformat()}..{end.isoformat()}"
    def q(extra: str) -> list[dict]:
        rs = "+".join(f"repo:{r}" for r in repos)
        # GitHub search requires an explicit is:issue / is:pull-request qualifier.
        return [i for kind in ("is:issue", "is:pull-request")
                for i in _gh(f"/search/issues?q={rs}+{kind}+{extra}&per_page=100", token)]
    def row(i):
        return {"repo": i["repository_url"].split("/repos/")[1], "number": i["number"], "title": i["title"],
                "url": i["html_url"], "kind": "PR" if "pull_request" in i else "issue",
                "labels": [l["name"] for l in i.get("labels", [])]}
    return {"opened": [row(i) for i in q(f"created:{rng}")],
            "closed": [row(i) for i in q(f"closed:{rng}")],
            "open_now": [row(i) for i in q("state:open")]}


def domain_expiry(names: list[str], fetch=None) -> list[dict]:
    """Days until registration expiry from RDAP (rdap.org bootstrap). Failures are reported, not hidden."""
    def _get(name):
        req = urllib.request.Request(f"https://rdap.org/domain/{name}", headers={"User-Agent": "edmhs-weekly"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.load(r)
    fetch = fetch or _get
    out = []
    for n in names:
        try:
            ev = {e["eventAction"]: e["eventDate"][:10] for e in fetch(n).get("events", [])}
            exp = ev.get("expiration")
            out.append({"domain": n, "expires": exp, "days_left": (date.fromisoformat(exp) - date.today()).days if exp else None})
        except Exception as e:
            out.append({"domain": n, "expires": None, "days_left": None, "error": type(e).__name__})
    return out


def render(end: date, sites: list[dict], tasks: dict | None, ndays: int, domains: list[dict] | None = None) -> str:
    yr, wk, _ = end.isocalendar()
    live = [s for s in sites if s["status_cfg"] == "live"]
    avail = round(sum(s["availability"] or 0 for s in live) / len(live), 1) if live else None
    out = [f"# Weekly site engineering report: {yr}-W{wk:02d} (through {end.isoformat()})", "",
           f"Daily reports found: **{ndays} of 7**. Mean availability of live sites: **{avail}%**." if avail is not None
           else f"Daily reports found: **{ndays} of 7**.", "",
           "## Sites", "", "| Site | Critical | Availability | Days | Trend (Mon→Sun) | Median ms | Cert days | Latest |",
           "|---|---|---|---|---|---|---|---|"]
    for s in sites:
        out.append(f"| [{s['name']}]({s['url']}) | {'yes' if s['critical'] else ''} | "
                   f"{'-' if s['availability'] is None else str(s['availability']) + '%'} | {s['up_days']}/{s['days']} | "
                   f"`{s['trend']}` | {s['median_ms'] or '-'} | {s['cert_days_left'] if s['cert_days_left'] is not None else '-'} | {s['latest']} |")
    out += ["", "Trend key: ▮ up · ▯ degraded · × down · · planned", ""]
    if domains:
        out += ["## Domains", "", "| Domain | Expires | Days left |", "|---|---|---|"]
        for d in domains:
            flag = " ⚠ renew" if d.get("days_left") is not None and d["days_left"] < 60 else ""
            out.append(f"| {d['domain']} | {d.get('expires') or 'lookup failed: ' + d.get('error', '?')} | "
                       f"{d['days_left'] if d.get('days_left') is not None else '-'}{flag} |")
        out.append("")
    out += ["## Problems this week", ""]
    probs = [(s["name"], p) for s in sites for p in s["problems"]]
    out += [f"- **{n}**: {p}" for n, p in probs] or ["- none"]
    out += ["", "## Engineering tasks", ""]
    if tasks is None:
        out.append("_Not collected: no GITHUB_TOKEN with read access to the task repositories, or no task_repos configured._")
    elif "error" in tasks:
        out.append(f"_Collection failed: {tasks['error']}. Site section above is complete._")
    else:
        for label, key in (("Opened this week", "opened"), ("Closed this week", "closed"), ("Open now", "open_now")):
            items = tasks[key]
            out += [f"### {label} ({len(items)})", ""]
            out += [f"- {i['kind']} [{i['repo']}#{i['number']}]({i['url']}): {i['title']}"
                    + (f" `{', '.join(i['labels'])}`" if i["labels"] else "") for i in items] or ["- none"]
            out.append("")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    here = Path(__file__).parent
    ap.add_argument("--sites", default=str(here / "sites.yaml"))
    ap.add_argument("--daily", default=str(here / "reports" / "daily"))
    ap.add_argument("--out", default=str(here / "reports" / "weekly"))
    ap.add_argument("--end", default=date.today().isoformat())
    a = ap.parse_args(argv)
    end = date.fromisoformat(a.end)
    cfg = yaml.safe_load(Path(a.sites).read_text())
    days = load_days(Path(a.daily), end)
    try:
        tasks = collect_tasks(cfg.get("task_repos", []), end - timedelta(days=6), end, os.getenv("GITHUB_TOKEN"))
    except Exception as e:  # report the gap; never lose the site section because GitHub was unreachable
        tasks = {"error": f"{type(e).__name__}: {e}"}
    doms = domain_expiry([d["name"] for d in cfg.get("domains", [])]) if cfg.get("domains") else None
    md = render(end, site_summary(days), tasks, len(days), doms)
    yr, wk, _ = end.isocalendar()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{yr}-W{wk:02d}.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
