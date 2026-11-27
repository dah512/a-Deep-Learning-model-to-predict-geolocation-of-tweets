"""Daily site review: checks every site in ops/sites.yaml and writes a dated report.

usage: python ops/sitecheck.py [--sites ops/sites.yaml] [--out ops/reports/daily] [--date YYYY-MM-DD]

Per site it checks: DNS, HTTP status, response time, expected content marker, TLS certificate
expiry, security headers, extra pages, same-site links on the home page, and an optional health URL.
Each site gets a verdict: UP, DEGRADED, DOWN or PLANNED, plus a severity for anything not UP.
Exit code is 1 when any live critical site is DOWN, so a scheduler can alert on it.
Standard library + PyYAML only.
"""
from __future__ import annotations

import argparse
import json
import socket
import ssl
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

import yaml

UA = "edmhs-sitecheck/1.0 (+https://edmhs.org)"
TIMEOUT = 15
SLOW_MS = 3000
CERT_WARN_DAYS = 21


class _Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)
        self._in_title = tag == "title"

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # report 3xx as-is (sign-in apps)
        return None


def fetch(url: str, follow: bool = True) -> dict:
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    t0 = time.perf_counter()
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            body = r.read(2_000_000).decode("utf-8", "replace")
            return {"status": r.status, "ms": round((time.perf_counter() - t0) * 1000), "body": body,
                    "headers": {k.lower(): v for k, v in r.headers.items()}, "final_url": r.geturl()}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "ms": round((time.perf_counter() - t0) * 1000), "body": "",
                "headers": {k.lower(): v for k, v in (e.headers or {}).items()}, "final_url": url}
    except Exception as e:  # DNS, TLS, timeout, refused
        return {"status": None, "ms": round((time.perf_counter() - t0) * 1000), "error": f"{type(e).__name__}: {e}"}


def cert_days_left(host: str, port: int = 443) -> int | None:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=TIMEOUT) as s, ctx.wrap_socket(s, server_hostname=host) as ts:
            exp = datetime.strptime(ts.getpeercert()["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            return (exp - datetime.now(timezone.utc)).days
    except Exception:
        return None


def check_site(site: dict) -> dict:
    url = site["url"]
    host = urlparse(url).hostname
    res = {"id": site["id"], "name": site["name"], "url": url, "critical": bool(site.get("critical")),
           "status_cfg": site.get("status", "live"), "checks": {}, "problems": []}
    expect = site.get("expect_status", [200])
    expect = expect if isinstance(expect, list) else [expect]

    try:
        socket.getaddrinfo(host, 443)
        res["checks"]["dns"] = "ok"
    except OSError as e:
        res["checks"]["dns"] = f"fail: {e}"

    r = fetch(url, follow=200 in expect and len(expect) == 1)
    res["checks"]["http_status"] = r["status"]
    res["checks"]["response_ms"] = r["ms"]
    if r["status"] is None:
        res["problems"].append(("down", f"no response: {r.get('error')}"))
    elif r["status"] not in expect:
        res["problems"].append(("down" if r["status"] >= 500 or r["status"] == 404 else "degraded",
                                f"HTTP {r['status']} (expected {expect})"))
    else:
        if r["ms"] > SLOW_MS:
            res["problems"].append(("degraded", f"slow: {r['ms']} ms"))
        body = r.get("body", "")
        if site.get("marker") and r["status"] == 200 and site["marker"] not in body:
            res["problems"].append(("degraded", f"content marker '{site['marker']}' missing (wrong or blank deploy?)"))
        hsts = "strict-transport-security" in r.get("headers", {})
        res["checks"]["hsts"] = hsts
        if url.startswith("https") and not hsts:
            res["problems"].append(("info", "no Strict-Transport-Security header"))

        if r["status"] == 200 and body:
            p = _Links()
            p.feed(body)
            res["checks"]["title"] = p.title.strip()[:120]
            same = sorted({urljoin(r["final_url"], h).split("#")[0] for h in p.links
                           if urlparse(urljoin(r["final_url"], h)).hostname == host})
            broken = []
            for link in same[:25]:
                lr = fetch(link)
                if lr["status"] is None or lr["status"] >= 400:
                    broken.append(f"{link} ({lr['status'] or lr.get('error', '?')})")
            res["checks"]["links_checked"] = len(same[:25])
            if broken:
                res["problems"].append(("degraded", "broken same-site links: " + "; ".join(broken)))

    for page in site.get("pages", []):
        pr = fetch(urljoin(url + "/", page.lstrip("/")))
        if pr["status"] != 200:
            res["problems"].append(("degraded", f"page {page}: HTTP {pr['status'] or pr.get('error')}"))

    if site.get("health_url"):
        hr = fetch(site["health_url"])
        res["checks"]["health"] = hr["status"]
        if hr["status"] != 200:
            res["problems"].append(("degraded", f"health endpoint: HTTP {hr['status'] or hr.get('error')}"))

    if url.startswith("https") and res["checks"]["dns"] == "ok" and r["status"] is not None:
        days = cert_days_left(host)
        res["checks"]["cert_days_left"] = days
        if days is not None and days < CERT_WARN_DAYS:
            res["problems"].append(("degraded" if days > 3 else "down", f"TLS certificate expires in {days} days"))

    kinds = {k for k, _ in res["problems"]}
    if res["status_cfg"] == "planned":
        verdict = "UP" if r["status"] in expect and "down" not in kinds else "PLANNED"
    else:
        verdict = "DOWN" if "down" in kinds else "DEGRADED" if "degraded" in kinds else "UP"
    res["verdict"] = verdict
    res["severity"] = None if verdict in ("UP", "PLANNED") else (
        "SEV1" if verdict == "DOWN" and res["critical"] else "SEV2" if verdict == "DOWN" or res["critical"] else "SEV3")
    res["problems"] = [{"kind": k, "detail": d} for k, d in res["problems"]]
    return res


def render_md(day: str, results: list[dict]) -> str:
    icon = {"UP": "🟢 UP", "DEGRADED": "🟡 DEGRADED", "DOWN": "🔴 DOWN", "PLANNED": "⚪ PLANNED"}
    up = sum(r["verdict"] == "UP" for r in results)
    live = sum(r["status_cfg"] == "live" for r in results)
    out = [f"# Daily site review: {day}", "",
           f"{up} of {len(results)} sites up ({live} live, {len(results) - live} planned).", "",
           "| Site | Verdict | Severity | HTTP | ms | Cert days | Problems |", "|---|---|---|---|---|---|---|"]
    for r in sorted(results, key=lambda x: ({"DOWN": 0, "DEGRADED": 1, "UP": 2, "PLANNED": 3}[x["verdict"]], x["id"])):
        c = r["checks"]
        probs = "; ".join(p["detail"] for p in r["problems"] if p["kind"] != "info") or "-"
        out.append(f"| [{r['name']}]({r['url']}) | {icon[r['verdict']]} | {r['severity'] or '-'} | "
                   f"{c.get('http_status') or '-'} | {c.get('response_ms', '-')} | {c.get('cert_days_left', '-')} | {probs} |")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sites", default=str(Path(__file__).with_name("sites.yaml")))
    ap.add_argument("--out", default=str(Path(__file__).parent / "reports" / "daily"))
    ap.add_argument("--date", default=date.today().isoformat())
    a = ap.parse_args(argv)
    cfg = yaml.safe_load(Path(a.sites).read_text())
    results = [check_site(s) for s in cfg["sites"]]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{a.date}.json").write_text(json.dumps({"date": a.date, "results": results}, indent=2))
    md = render_md(a.date, results)
    (out / f"{a.date}.md").write_text(md)
    print(md)
    return 1 if any(r["severity"] == "SEV1" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
