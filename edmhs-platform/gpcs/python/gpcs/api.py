"""FastAPI service for GPCS (consumed by the React UI)."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .applicant import PROFILE_CLASSES
from .crosswalk import build_crosswalk
from .draft import draft_sections
from .knowledge import KnowledgeBase
from .solicitation import parse

KB_ROOT = Path(os.getenv("GPCS_KB", Path(__file__).resolve().parents[3] / "knowledge_base"))
app = FastAPI(title="GPCS", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
                   allow_methods=["*"], allow_headers=["*"])


def _orgs() -> list[str]:
    return sorted(p.stem for p in (KB_ROOT / "organizations").glob("*.yaml"))


@app.get("/health")
def health():
    return {"ok": True, "kb": str(KB_ROOT), "orgs": _orgs()}


@app.get("/intake/{applicant_type}")
def intake(applicant_type: str):
    cls = PROFILE_CLASSES.get(applicant_type)
    if not cls:
        raise HTTPException(404, "applicant_type must be nonprofit or for_profit")
    return {"applicant_type": applicant_type, "rules": cls.rules, "questions": [q.__dict__ for q in cls.questions]}


@app.get("/profiles/{org}")
def profile(org: str):
    if org not in _orgs():
        raise HTTPException(404, f"unknown org; choose from {_orgs()}")
    from .applicant import load_profile
    p = load_profile(KB_ROOT / "organizations" / f"{org}.yaml")
    return {"applicant_type": p.applicant_type, "readiness": p.readiness(), "intake": p.intake_form()}


async def _parse_upload(f: UploadFile):
    suffix = Path(f.filename or "x.pdf").suffix or ".pdf"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await f.read())
    try:
        return parse(tmp.name)
    finally:
        os.unlink(tmp.name)


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    return (await _parse_upload(file)).to_dict()


@app.post("/crosswalk")
async def crosswalk(org: str, program: str, file: UploadFile = File(...)):
    sol = await _parse_upload(file)
    cw = build_crosswalk(sol, KnowledgeBase.load(KB_ROOT, org, program))
    return {"solicitation": sol.to_dict(), "crosswalk": cw.to_dict(), "markdown": cw.to_markdown()}


@app.post("/draft")
async def draft(org: str, program: str, mode: str = "template", file: UploadFile = File(...)):
    sol = await _parse_upload(file)
    secs = draft_sections(sol, KnowledgeBase.load(KB_ROOT, org, program), mode=mode)
    return {"sections": [s.__dict__ for s in secs]}
