"""Parse a funding solicitation (Grants.gov listing, forecast or full NOFO) into structured data.

Works on PDF or plain text. Extraction is rule-based and deterministic, so the output is auditable.
Fields that cannot be found stay ``None`` and are reported in ``missing``, never guessed.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# Grants.gov eligibility vocabulary, grouped so profiles can test membership.
ELIGIBILITY_GROUPS = {
    "nonprofit": [
        "Nonprofits non-higher education with 501(c)(3)",
        "Nonprofits non-higher education without 501(c)(3)",
        "Other Native American tribal organizations",
    ],
    "for_profit": [
        "Small businesses",
        "For-profit organizations other than small businesses",
    ],
    "government": [
        "State governments", "County governments", "City or township governments",
        "Special district governments", "Federally recognized Native American tribal governments",
        "Public and Indian housing authorities",
    ],
    "education": [
        "Public and state institutions of higher education",
        "Private institutions of higher education", "Independent school districts",
    ],
    "other": ["Unrestricted", "Other", "Individuals"],
}
_ALL_ELIG = {item: grp for grp, items in ELIGIBILITY_GROUPS.items() for item in items}

_REQ_VERBS = re.compile(r"\b(must|should|shall|required|are expected to|will (?:address|conduct|establish|foster|integrate))\b", re.I)


@dataclass
class CoreElement:
    number: int
    name: str
    text: str


@dataclass
class Solicitation:
    title: Optional[str] = None
    agency: Optional[str] = None
    opportunity_number: Optional[str] = None
    status: Optional[str] = None  # forecasted | posted | closed | archived
    assistance_listings: list[str] = field(default_factory=list)
    dates: dict[str, str] = field(default_factory=dict)
    fiscal_year: Optional[int] = None
    total_funding: Optional[int] = None
    expected_awards: Optional[int] = None
    award_floor: Optional[int] = None
    award_ceiling: Optional[int] = None
    cost_sharing: Optional[bool] = None
    instrument: Optional[str] = None
    category: Optional[str] = None
    eligibility: list[str] = field(default_factory=list)
    population_ages: Optional[tuple[int, int]] = None
    core_elements: list[CoreElement] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    contacts: list[str] = field(default_factory=list)
    summary: Optional[str] = None
    is_research: bool = False
    missing: list[str] = field(default_factory=list)

    # ---- derived ----
    @property
    def eligible_groups(self) -> set[str]:
        return {_ALL_ELIG[e] for e in self.eligibility if e in _ALL_ELIG}

    def eligible_for(self, applicant_type: str) -> bool:
        groups = self.eligible_groups
        return applicant_type in groups or "other" in groups and "Unrestricted" in self.eligibility

    @property
    def implied_years(self) -> Optional[float]:
        """Total funding / (awards * ceiling): ~ project period in years when the ceiling is annual."""
        if self.total_funding and self.expected_awards and self.award_ceiling:
            return round(self.total_funding / (self.expected_awards * self.award_ceiling), 2)
        return None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["eligible_groups"] = sorted(self.eligible_groups)
        d["implied_years"] = self.implied_years
        return d


def read_text(path: str | Path) -> str:
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader

        return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8", errors="replace")


def _clean(text: str) -> str:
    text = text.replace("\xa0", " ").replace("’", "'")
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln and ln not in {"●", "○", "•"})


def _money(s: str | None) -> Optional[int]:
    if not s:
        return None
    m = re.search(r"\$?\s*([\d,]+(?:\.\d+)?)", s)
    return int(float(m.group(1).replace(",", ""))) if m else None


def _after(label: str, text: str) -> Optional[str]:
    """Value on the same line after 'label:' or on the next line."""
    m = re.search(rf"{label}\s*:?[ \t]*([^\n]*)\n?([^\n]*)", text, re.I)
    if not m:
        return None
    val = m.group(1).strip() or m.group(2).strip()
    return val or None


def _flow(block: str) -> str:
    return re.sub(r"\s*\n\s*", " ", block).strip()


def parse_text(raw: str) -> Solicitation:
    t = _clean(raw)
    s = Solicitation()

    # Title: everything before "Agency:"
    m = re.search(r"^(.*?)\nAgency:", t, re.S)
    if m:
        s.title = _flow(m.group(1).split("\n\n")[-1])
    s.agency = _after("Agency", t)
    s.assistance_listings = [
        f"{a} -- {_flow(b)}" for a, b in re.findall(r"(\d{2}\.\d{3})\s*--\s*(.+?(?:\n[a-z].*?)?)(?=\n[A-Z][a-z]+\n|\nForecast|\nPosted|$)", t)
    ]
    if not s.assistance_listings:
        s.assistance_listings = re.findall(r"\b(\d{2}\.\d{3})\b", t)[:3]

    for status in ("Forecasted", "Posted", "Closed", "Archived"):
        if re.search(rf"^{status}\b", t, re.M):
            s.status = status.lower()
            break

    for key, label in {
        "post": r"(?:Forecasted )?post(?:ed)? date",
        "due": r"(?:Forecasted )?(?:application due|close) date",
        "award": r"(?:Forecasted )?award date",
        "start": r"(?:Forecasted )?project start date",
        "archive": r"Archive date",
        "last_updated": r"Last Updated",
    }.items():
        mm = re.search(rf"{label}\s*:\s*([A-Z][a-z]+\.? \d{{1,2}}, \d{{4}})", t, re.I)
        if mm:
            s.dates[key] = mm.group(1)

    fy = _after("Fiscal Year", t)
    s.fiscal_year = int(re.search(r"\d{4}", fy).group()) if fy and re.search(r"\d{4}", fy) else None
    s.total_funding = _money(_after(r"(?:Expected project funding|Estimated Total Program Funding)", t))
    aw = _after(r"(?:Expected awards|Expected Number of Awards)", t)
    s.expected_awards = int(re.sub(r"\D", "", aw)) if aw and re.search(r"\d", aw) else None
    s.award_floor = _money(_after(r"Award (?:min\.?|Floor)", t))
    s.award_ceiling = _money(_after(r"Award (?:max\.?|Ceiling)", t))
    s.opportunity_number = _after(r"Funding opportunity number", t)
    cs = _after(r"Cost sharing or matching requirement", t)
    s.cost_sharing = None if cs is None else cs.lower().startswith("y")
    s.instrument = _after(r"Funding instrument type", t)
    s.category = _after(r"Category of Funding Activity", t)

    # Eligibility: known vocabulary lines between "Eligibility" and "Additional information"
    em = re.search(r"\nEligibility\n(.*?)(?:\nAdditional information on eligibility|\nDocuments\n|$)", t, re.S)
    block = em.group(1) if em else t
    s.eligibility = [ln for ln in block.split("\n") if ln.strip() in _ALL_ELIG]

    am = re.search(r"aged?\s+(\d{1,2})\s*(?:to|-|–|through)\s*(\d{1,2})", t)
    if am:
        s.population_ages = (int(am.group(1)), int(am.group(2)))

    sm = re.search(r"\nSummary\n(.*?)(?:\nEligibility\n|$)", t, re.S)
    if sm:
        s.summary = _flow(sm.group(1))
        body = s.summary
        for num, name, txt in re.findall(r"(\d)\)\s*([A-Z][A-Za-z ]+?):\s*(.*?)(?=\s\d\)\s*[A-Z]|$)", body):
            s.core_elements.append(CoreElement(int(num), name.strip(), txt.strip()))
        sentences = re.split(r"(?<=[.;])\s+(?=[A-Z0-9])", body)
        s.requirements = [x.strip() for x in sentences if _REQ_VERBS.search(x)]

    s.contacts = sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", t)))
    s.is_research = bool(re.search(r"\b(RFA|PAR|PA)-[A-Z]{2}-\d{2}-\d{3}\b", s.opportunity_number or "")) or bool(
        re.search(r"investigator-initiated research|rigorous evaluation", t, re.I)
    )
    for f in ("title", "agency", "opportunity_number", "award_ceiling", "instrument"):
        if getattr(s, f) in (None, "", []):
            s.missing.append(f)
    if "due" not in s.dates:
        s.missing.append("dates.due")
    return s


def parse(path: str | Path) -> Solicitation:
    return parse_text(read_text(path))
