"""Compliance crosswalk: solicitation requirements -> package components -> knowledge-base coverage."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

from .knowledge import KnowledgeBase
from .packages import Component, Package, select_package
from .solicitation import Solicitation


@dataclass
class Row:
    requirement: str
    source: str  # core_element | requirement | eligibility | award
    components: list[str] = field(default_factory=list)
    status: str = "unmapped"  # facts available | partial | gap | needs narrative | unmapped | blocker


@dataclass
class Crosswalk:
    solicitation: str
    applicant_type: str
    package: str
    eligible: bool
    rows: list[Row]
    component_status: dict[str, dict]
    profile_gaps: list[dict]
    flags: list[str]

    def to_dict(self) -> dict:
        return asdict(self)

    def to_markdown(self) -> str:
        out = [f"# Compliance crosswalk: {self.solicitation}", "",
               f"Applicant type: **{self.applicant_type}** · Package: **{self.package}** · "
               f"Eligible: **{'yes' if self.eligible else 'NO'}**", ""]
        if self.flags:
            out += ["## Flags", *[f"- {f}" for f in self.flags], ""]
        out += ["## Requirements", "", "| # | Requirement | Source | Components | Status |", "|---|---|---|---|---|"]
        for i, r in enumerate(self.rows, 1):
            req = r.requirement.replace("|", "/")
            req = req if len(req) < 160 else req[:157] + "..."
            out.append(f"| {i} | {req} | {r.source} | {', '.join(r.components) or '-'} | {r.status} |")
        out += ["", "## Package components", "", "| Component | Kind | Required | KB coverage | Missing KB keys |",
                "|---|---|---|---|---|"]
        for cid, st in self.component_status.items():
            out.append(f"| {st['title']} | {st['kind']} | {'yes' if st['required'] else 'no'} | "
                       f"{st['coverage']:.0%} | {', '.join(st['missing']) or '-'} |")
        out += ["", "## Applicant intake gaps", ""]
        out += [f"- **{g['key']}**: {g['prompt']} ({g['why']})" for g in self.profile_gaps] or ["- none"]
        return "\n".join(out) + "\n"


def _tokens(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", s.lower())}


def _match(text: str, comps: list[Component]) -> list[str]:
    low = text.lower()
    hits = [c.id for c in comps if any(a.lower() in low for a in c.answers)]
    if hits:
        return hits
    # fallback: best token overlap with component title + answers
    tt = _tokens(text)
    scored = sorted(((len(tt & _tokens(c.title + " " + " ".join(c.answers))), c.id) for c in comps), reverse=True)
    return [scored[0][1]] if scored and scored[0][0] >= 2 else []


def build_crosswalk(sol: Solicitation, kb: KnowledgeBase, package: Package | None = None) -> Crosswalk:
    package = package or select_package(sol)
    atype = kb.profile.applicant_type
    comps = package.for_applicant(atype)

    comp_status: dict[str, dict] = {}
    for c in comps:
        missing = [k for k in c.kb_keys if not kb.has(k)]
        cov = 1.0 if not c.kb_keys else 1 - len(missing) / len(c.kb_keys)
        comp_status[c.id] = {"title": c.title, "kind": c.kind, "required": c.required,
                             "coverage": round(cov, 2), "missing": missing, "kb_keys": list(c.kb_keys)}

    def status_for(ids: list[str]) -> str:
        if not ids:
            return "unmapped"
        if not any(comp_status[i]["kb_keys"] for i in ids):
            return "needs narrative"  # no KB facts back these components; must be written
        covs = [comp_status[i]["coverage"] for i in ids if comp_status[i]["kb_keys"]]
        return "facts available" if min(covs) >= 1 else "partial" if max(covs) > 0 else "gap"

    rows: list[Row] = []
    for ce in sol.core_elements:
        ids = _match(ce.name + " " + ce.text, comps)
        rows.append(Row(f"Core element {ce.number} - {ce.name}: {ce.text}", "core_element", ids, status_for(ids)))
    seen = {r.requirement for r in rows}
    for req in sol.requirements:
        if any(req in s for s in seen) or any(ce.name in req for ce in sol.core_elements):
            continue  # already represented by a core-element row
        ids = _match(req, comps)
        rows.append(Row(req, "requirement", ids, status_for(ids)))

    eligible = sol.eligible_for(atype) if sol.eligibility else True
    rows.append(Row(f"Eligibility: applicant type '{atype}' in {sorted(sol.eligible_groups)}", "eligibility",
                    ["sf424_rr" if package.id == "sf424_rr" else "sf424"], "eligible" if eligible else "blocker"))

    flags: list[str] = []
    if not eligible:
        flags.append(f"BLOCKER: '{atype}' applicants are not eligible for this opportunity.")
    if sol.status == "forecasted":
        flags.append("Forecast only: re-run GPCS on the full NOFO when it posts "
                     f"({sol.dates.get('post', 'date TBD')}); page limits and scoring criteria will change.")
    if sol.implied_years and sol.implied_years > 1.2:
        flags.append(f"Total funding / (awards x ceiling) = {sol.implied_years}: the ceiling is probably per budget "
                     f"year (~{round(sol.implied_years)}-year project period).")
    if sol.population_ages:
        prog_ages = (kb.program.get("population") or {}).get("current_ages")
        lo, hi = sol.population_ages
        if prog_ages and (prog_ages[0] > lo or prog_ages[1] < hi):
            flags.append(f"Population mismatch: solicitation targets ages {lo}-{hi}; program currently serves "
                         f"{prog_ages[0]}-{prog_ages[1]}. Narrative must describe the extension.")
    if kb.profile.applicant_type == "for_profit":
        flags.append("For-profit applicant: budget must exclude profit/fee (2 CFR 200.400(g)).")
    for k in ("uei", "sam_status"):
        if not kb.has(f"org.{k}"):
            flags.append(f"BLOCKER until resolved: org.{k} missing - SAM.gov registration takes 2-6 weeks.")
    if sol.cost_sharing is False:
        flags.append("No cost sharing required; do not volunteer committed cost share (it becomes auditable).")

    return Crosswalk(
        solicitation=f"{sol.opportunity_number or '?'} - {sol.title or '?'}",
        applicant_type=atype, package=package.name, eligible=eligible, rows=rows,
        component_status=comp_status,
        profile_gaps=[{"key": q.key, "prompt": q.prompt, "why": q.why} for q in kb.profile.gaps()],
        flags=flags,
    )
