"""Site check + weekly aggregation tests against a local HTTP server (no internet needed)."""
import http.server
import json
import sys
import threading
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import sitecheck  # noqa: E402
import weekly  # noqa: E402

PAGES = {
    "/": (200, '<html><title>Good Site</title><a href="/ok">ok</a><a href="/missing">x</a><a href="https://other.example/">ext</a></html>'),
    "/ok": (200, "fine"),
    "/clean": (200, '<html><title>Clean</title>Inner Combat Training <a href="/ok">ok</a></html>'),
    "/boom": (500, "error"),
    "/health": (200, '{"ok":true}'),
}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        code, body = PAGES.get(self.path, (404, "nope"))
        self.send_response(code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def base():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def site(url, **kw):
    return {"id": kw.pop("id", "t"), "name": "Test", "url": url, **kw}


def test_up_clean(base):
    r = sitecheck.check_site(site(base + "/clean", marker="Inner Combat Training", health_url=base + "/health", critical=True))
    assert r["verdict"] == "UP" and r["severity"] is None
    assert r["checks"]["title"] == "Clean" and r["checks"]["health"] == 200


def test_broken_link_and_missing_marker_degrade(base):
    r = sitecheck.check_site(site(base + "/", marker="Inner Combat Training"))
    details = " ".join(p["detail"] for p in r["problems"])
    assert r["verdict"] == "DEGRADED" and r["severity"] == "SEV3"
    assert "marker" in details and "/missing" in details and "other.example" not in details


def test_server_error_is_down_and_sev1_when_critical(base):
    r = sitecheck.check_site(site(base + "/boom", critical=True))
    assert r["verdict"] == "DOWN" and r["severity"] == "SEV1"


def test_unreachable_is_down(base):
    r = sitecheck.check_site(site("http://127.0.0.1:9/"))
    assert r["verdict"] == "DOWN" and "no response" in r["problems"][0]["detail"]


def test_planned_site_never_fails(base):
    r = sitecheck.check_site(site("http://127.0.0.1:9/", status="planned", critical=True))
    assert r["verdict"] == "PLANNED" and r["severity"] is None


def test_sign_in_redirect_accepted(base):
    r = sitecheck.check_site(site(base + "/missing", expect_status=[200, 302, 401, 404]))
    assert r["verdict"] == "UP"


def test_daily_then_weekly(base, tmp_path):
    cfg = tmp_path / "sites.yaml"
    cfg.write_text(f"sites:\n  - {{id: a, name: A, url: '{base}/clean', critical: true}}\n"
                   f"  - {{id: b, name: B, url: '{base}/boom'}}\ntask_repos: []\n")
    end = date(2026, 11, 29)
    daily = tmp_path / "daily"
    for i in range(7):
        d = (end - timedelta(days=6 - i)).isoformat()
        assert sitecheck.main(["--sites", str(cfg), "--out", str(daily), "--date", d]) == 0  # b is DOWN but not critical
    data = json.loads((daily / "2026-11-29.json").read_text())
    assert {r["id"]: r["verdict"] for r in data["results"]} == {"a": "UP", "b": "DOWN"}
    assert weekly.main(["--sites", str(cfg), "--daily", str(daily), "--out", str(tmp_path / "wk"), "--end", end.isoformat()]) == 0
    md = (tmp_path / "wk" / "2026-W48.md").read_text()
    assert "7 of 7" in md and "100.0%" in md and "0.0%" in md and "`×××××××`" in md
    assert "Not collected" in md   # no token -> explicit, not zero


def test_sev1_exit_code(base, tmp_path):
    cfg = tmp_path / "s.yaml"
    cfg.write_text(f"sites:\n  - {{id: a, name: A, url: '{base}/boom', critical: true}}\n")
    assert sitecheck.main(["--sites", str(cfg), "--out", str(tmp_path), "--date", "2026-11-27"]) == 1


def test_incident_lifecycle():
    import incidents
    issues, calls = {}, []
    def fake(method, path, body=None):
        calls.append((method, path))
        if method == "GET":
            return [v for v in issues.values() if v["state"] == "open"]
        if method == "POST" and path.endswith("/issues"):
            n = len(issues) + 1
            issues[n] = {"number": n, "title": body["title"], "state": "open", "labels": body["labels"]}
        if method == "PATCH":
            issues[int(path.rsplit("/", 1)[1])]["state"] = body["state"]
    down = {"date": "2026-11-28", "results": [{"id": "ict", "url": "u", "verdict": "DOWN", "severity": "SEV1",
             "problems": [{"kind": "down", "detail": "HTTP 500"}]}]}
    up = {"date": "2026-11-30", "results": [{"id": "ict", "url": "u", "verdict": "UP", "severity": None, "problems": []}]}
    assert incidents.sync(down, "o/r", fake)["opened"] == ["ict"]
    assert issues[1]["labels"] == ["site-incident", "sev1"]
    assert incidents.sync(down, "o/r", fake)["updated"] == ["ict"]          # no duplicate issue
    assert incidents.sync(up, "o/r", fake)["closed"] == ["ict"] and issues[1]["state"] == "closed"


def test_domain_expiry_and_failure():
    rd = {"events": [{"eventAction": "expiration", "eventDate": "2099-01-01T00:00:00Z"}]}
    ok, bad = weekly.domain_expiry(["edmhs.org", "x.invalid"], fetch=lambda n: rd if n == "edmhs.org" else 1 / 0)
    assert ok["expires"] == "2099-01-01" and ok["days_left"] > 1000
    assert bad["days_left"] is None and bad["error"] == "ZeroDivisionError"
