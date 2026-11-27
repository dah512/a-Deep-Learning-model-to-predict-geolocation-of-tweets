"""Applicant profiles: separate structures for nonprofit and for-profit applicants.

Each profile class declares the intake questions it needs (what the system must solicit) and the
federal rules that apply. ``load_profile`` builds the right class from a knowledge-base YAML file.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import yaml


@dataclass(frozen=True)
class Question:
    key: str
    prompt: str
    why: str
    required: bool = True


_COMMON = (
    Question("legal_name", "Legal name exactly as registered in SAM.gov", "SF424 item 8a must match SAM"),
    Question("uei", "Unique Entity ID (UEI)", "Required for all federal awards (2 CFR 25)"),
    Question("ein", "Employer Identification Number", "SF424 item 8b"),
    Question("sam_status", "SAM.gov registration status and expiration", "Must be active at submission and award"),
    Question("address", "Applicant address, county, congressional district", "SF424; site locations"),
    Question("mission", "Mission statement", "Organizational capacity narrative"),
    Question("leadership", "Program director / PI and key personnel", "Key person profiles; biosketches"),
    Question("partners", "Partners and status of each letter of support", "Collaboration narrative; letters"),
    Question("financials.indirect_rate", "Negotiated indirect rate, or de minimis 15% MTDC", "Budget F&A (2 CFR 200.414)"),
)


@dataclass
class ApplicantProfile:
    data: dict[str, Any]
    applicant_type: ClassVar[str] = "base"
    questions: ClassVar[tuple[Question, ...]] = _COMMON
    rules: ClassVar[tuple[str, ...]] = ()

    def get(self, dotted: str, default=None):
        cur: Any = self.data
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return default
            cur = cur[part]
        return cur

    @staticmethod
    def _is_blank(v) -> bool:
        return v in (None, "", [], {}) or (isinstance(v, str) and (v.startswith("TODO") or "not registered" in v))

    def gaps(self) -> list[Question]:
        """Required intake questions not yet answered in the knowledge base."""
        return [q for q in self.questions if q.required and self._is_blank(self.get(q.key))]

    def readiness(self) -> float:
        req = [q for q in self.questions if q.required]
        return round(1 - len(self.gaps()) / len(req), 2) if req else 1.0

    def intake_form(self) -> list[dict]:
        return [
            {"key": q.key, "prompt": q.prompt, "why": q.why, "required": q.required,
             "current": None if self._is_blank(self.get(q.key)) else self.get(q.key)}
            for q in self.questions
        ]


@dataclass
class NonprofitProfile(ApplicantProfile):
    applicant_type: ClassVar[str] = "nonprofit"
    questions: ClassVar[tuple[Question, ...]] = _COMMON + (
        Question("tax_status", "501(c)(3) determination letter, or nonprofit without 501(c)(3)",
                 "Selects the Grants.gov eligibility category"),
        Question("board", "Governing board roster (names, affiliations, community representation)",
                 "Capacity; community governance", required=False),
        Question("financials.audit", "Most recent audit; Single Audit status",
                 "2 CFR 200.501: Single Audit if >= $1,000,000 federal expenditures/yr"),
        Question("financials.annual_budget", "Annual operating budget", "Financial capacity vs. award size"),
    )
    rules: ClassVar[tuple[str, ...]] = (
        "Cost principles: 2 CFR 200 Subpart E (HHS: 45 CFR 75 / 2 CFR 300)",
        "Single Audit (2 CFR 200 Subpart F) if federal expenditures >= $1,000,000 in a fiscal year",
        "Indirect: negotiated rate or de minimis 15% of MTDC (2 CFR 200.414(f))",
        "Program income and lobbying restrictions apply (2 CFR 200.307; 45 CFR 93)",
    )


@dataclass
class ForProfitProfile(ApplicantProfile):
    applicant_type: ClassVar[str] = "for_profit"
    questions: ClassVar[tuple[Question, ...]] = _COMMON + (
        Question("business_size", "Small business status for the primary NAICS code (SBA size standard)",
                 "Selects 'Small businesses' vs 'For-profit other than small' eligibility"),
        Question("naics", "Primary NAICS code", "Size standard lookup"),
        Question("ownership", "Owners >= 25% and any foreign ownership/control", "Responsibility review; FAPIIS"),
        Question("financials.statements", "Financial statements, last 2 fiscal years", "Financial capability / risk review"),
        Question("cage", "CAGE code", "SAM registration detail", required=False),
    )
    rules: ClassVar[tuple[str, ...]] = (
        "No profit or fee on grants/cooperative agreements (2 CFR 200.400(g); 45 CFR 75.216(b))",
        "Cost principles for commercial organizations: FAR 31.2 (48 CFR 31.2)",
        "HHS audit requirements for for-profits: 45 CFR 75.216 / 75.501(i)",
        "Indirect: negotiated rate or de minimis 15% of MTDC",
    )


PROFILE_CLASSES = {c.applicant_type: c for c in (NonprofitProfile, ForProfitProfile)}


def load_profile(path: str | Path) -> ApplicantProfile:
    data = yaml.safe_load(Path(path).read_text())
    kind = data.get("applicant_type")
    if kind not in PROFILE_CLASSES:
        raise ValueError(f"applicant_type must be one of {sorted(PROFILE_CLASSES)}, got {kind!r}")
    return PROFILE_CLASSES[kind](data)
