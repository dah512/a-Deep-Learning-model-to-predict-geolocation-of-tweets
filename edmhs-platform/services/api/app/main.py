"""EDMHS backend API: ICT intake, KATA collaboration, de-identified analytics, and GPCS.

Each route uses a database login bound to the least-privileged group role it needs:
  INTAKE_DATABASE_URL    -> member of edm_intake      (enrollment requests)
  ANALYTICS_DATABASE_URL -> member of edm_analyst     (de-identified aggregates only)
Contact and health fields are encrypted with pgp_sym_encrypt; the key (PII_KEY) lives in the app
environment / secret manager, never in the database.
"""
from __future__ import annotations

import os
import re
from datetime import date
from typing import Literal, Optional

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field, field_validator

from gpcs.api import app as gpcs_app

SERVICE_ZIPS = {"43607", "43610", "43620"}
app = FastAPI(title="EDMHS API", version="0.1.0")
app.add_middleware(CORSMiddleware,
                   allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,https://ict.edmhs.us,https://ict.edmhs.org,https://edmhs.org,https://www.edmhs.org").split(","),
                   allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
app.mount("/gpcs", gpcs_app)


def _conn(env: str):
    url = os.getenv(env)
    if not url:
        raise HTTPException(503, f"{env} not configured")
    return psycopg.connect(url)


def age_on(dob: date, on: date) -> int:
    return on.year - dob.year - ((on.month, on.day) < (dob.month, dob.day))


class EnrollmentRequest(BaseModel):
    child_first: str = Field(min_length=1, max_length=80)
    child_last: str = Field(min_length=1, max_length=80)
    dob: date
    home_zip: str
    preferred_cohort: Literal["any", "Monday", "Tuesday", "Wednesday", "Thursday"] = "any"
    guardian_name: Optional[str] = Field(default=None, max_length=120)
    relationship: Optional[str] = Field(default=None, max_length=60)
    phone: str
    email: Optional[EmailStr] = None
    health_notes: Optional[str] = Field(default=None, max_length=2000)
    attest_guardian_or_adult: bool

    @field_validator("home_zip")
    @classmethod
    def _zip(cls, v: str) -> str:
        if v not in SERVICE_ZIPS:
            raise ValueError(f"service area is {sorted(SERVICE_ZIPS)}")
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) not in (10, 11):
            raise ValueError("phone must have 10 digits")
        return digits[-10:]


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ict/enroll", status_code=201)
def enroll(req: EnrollmentRequest):
    if not req.attest_guardian_or_adult:
        raise HTTPException(422, "guardian (or adult participant) attestation is required")
    age = age_on(req.dob, date.today())
    if not 6 <= age <= 24:
        raise HTTPException(422, "ICT serves ages 6-24 (YVPC research arm: 10-24)")
    if age < 18 and not (req.guardian_name and req.relationship):
        raise HTTPException(422, "guardian name and relationship are required for participants under 18")
    key = os.getenv("PII_KEY")
    if not key:
        raise HTTPException(503, "PII_KEY not configured")
    with _conn("INTAKE_DATABASE_URL") as con, con.cursor() as cur:
        cur.execute(
            """INSERT INTO intake.participant (first_name, last_name, dob, home_zip, phone_enc, health_notes_enc)
               VALUES (%s, %s, %s, %s, pgp_sym_encrypt(%s, %s),
                       CASE WHEN %s::text IS NULL THEN NULL ELSE pgp_sym_encrypt(%s, %s) END)
               RETURNING participant_id""",
            (req.child_first, req.child_last, req.dob, req.home_zip, req.phone, key,
             req.health_notes, req.health_notes, key))
        pid = cur.fetchone()[0]
        if age < 18:
            cur.execute("INSERT INTO intake.guardian (participant_id, full_name, relationship, phone, email) "
                        "VALUES (%s, %s, %s, %s, %s)",
                        (pid, req.guardian_name, req.relationship, req.phone, req.email))
        cur.execute("INSERT INTO intake.enrollment (participant_id, program_id, status) "
                    "SELECT %s, program_id, 'requested' FROM core.program WHERE slug = 'ict'", (pid,))
    # Never echo identifiers back; the intake coordinator calls the family.
    return {"status": "requested", "next_step": "An intake coordinator will call to confirm and place your child. "
            "Consent and health forms are signed in person at the first session."}


@app.get("/analytics/enrollment-summary")
def enrollment_summary():
    """Aggregates only, with small-cell suppression (n < 5 shown as '<5')."""
    with _conn("ANALYTICS_DATABASE_URL") as con, con.cursor() as cur:
        cur.execute("""SELECT program, coalesce(dev_band, 'unassigned'), home_zip, count(*)
                       FROM analytics.participant_deid GROUP BY 1, 2, 3 ORDER BY 1, 2, 3""")
        rows = cur.fetchall()
    return [{"program": p, "dev_band": b, "zip": z, "n": n if n >= 5 else "<5"} for p, b, z, n in rows]


# Entry point for Cloud Run behind Firebase Hosting, which forwards /api/** unchanged.
# Serves the same routes at /api/... (hosting rewrite) and at / (direct or compose nginx).
served = FastAPI(title="EDMHS API (served)", version=app.version, docs_url=None, redoc_url=None)
served.mount("/api", app)
served.mount("/", app)
