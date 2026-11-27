"""Integration tests: need a live database loaded with db/init and env vars set (see README)."""
import os
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.main import age_on, app

pytestmark = pytest.mark.skipif(not os.getenv("INTAKE_DATABASE_URL"), reason="no database configured")
client = TestClient(app)


def body(**kw):
    b = dict(child_first="Test", child_last="Child", dob="2014-03-02", home_zip="43610", phone="(419) 555-0100",
             guardian_name="Test Parent", relationship="mother", attest_guardian_or_adult=True)
    b.update(kw)
    return b


def test_age_on():
    assert age_on(date(2010, 6, 1), date(2026, 5, 31)) == 15
    assert age_on(date(2010, 6, 1), date(2026, 6, 1)) == 16


def test_enroll_ok_and_no_pii_echo():
    r = client.post("/ict/enroll", json=body())
    assert r.status_code == 201, r.text
    assert "Test" not in r.text and "555" not in r.text


@pytest.mark.parametrize("kw,code", [({"home_zip": "43604"}, 422), ({"attest_guardian_or_adult": False}, 422),
                                     ({"guardian_name": None}, 422), ({"dob": "1990-01-01"}, 422)])
def test_enroll_rejections(kw, code):
    assert client.post("/ict/enroll", json=body(**kw)).status_code == code


def test_adult_peer_mentor_without_guardian():
    r = client.post("/ict/enroll", json=body(dob="2005-01-01", guardian_name=None, relationship=None))
    assert r.status_code == 201


def test_summary_suppresses_small_cells():
    rows = client.get("/analytics/enrollment-summary").json()
    assert rows and all(r["n"] == "<5" or r["n"] >= 5 for r in rows)
