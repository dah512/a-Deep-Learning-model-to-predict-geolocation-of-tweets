"""Standard federal application package structures.

Each package is a list of *components*: a form, a narrative section or an attachment. Each component
says what knowledge-base facts it draws on (``kb_keys``) and which solicitation requirements it usually
answers (``answers``: keywords matched against requirement text and core elements).
Page limits are defaults and are overridden by the NOFO when GPCS parses one.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Component:
    id: str
    title: str
    kind: str  # form | narrative | attachment
    required: bool = True
    page_limit: float | None = None
    kb_keys: tuple[str, ...] = ()
    answers: tuple[str, ...] = ()
    applies_to: tuple[str, ...] = ("nonprofit", "for_profit")
    guidance: str = ""


@dataclass(frozen=True)
class Package:
    id: str
    name: str
    used_for: str
    components: tuple[Component, ...] = field(default_factory=tuple)

    def for_applicant(self, applicant_type: str) -> list[Component]:
        return [c for c in self.components if applicant_type in c.applies_to]


SF424_RR = Package(
    id="sf424_rr",
    name="SF424 (R&R) research package (NIH/CDC eRA)",
    used_for="Research RFAs/PAs (CDC CE, NIH): investigator-initiated research, cooperative agreements",
    components=(
        Component("sf424_rr", "SF424 (R&R) cover", "form", kb_keys=("org.legal_name", "org.uei", "org.ein", "org.address"),
                  guidance="Applicant org, UEI, PD/PI, project period, funds requested, AOR signature."),
        Component("sites", "Project/Performance Site Locations", "form", kb_keys=("org.address", "program.population.zip_codes")),
        Component("abstract", "Project Summary/Abstract", "narrative", page_limit=1, kb_keys=("program.summary",),
                  answers=("purpose", "population", "approach"), guidance="<= 30 lines; aims, methods, community, outcomes."),
        Component("narrative", "Project Narrative (public health relevance)", "narrative", page_limit=1/6,
                  answers=("public health",), guidance="2-3 sentences, lay language."),
        Component("aims", "Specific Aims", "narrative", page_limit=1, answers=("evaluation", "approaches", "priority research")),
        Component("strategy", "Research Strategy", "narrative", page_limit=12,
                  kb_keys=("program.summary", "program.developmental_bands", "evidence"),
                  answers=("rigorous evaluation", "priority research", "approaches", "Research and Rigorous Evaluation",
                           "communities with rates", "higher than the national average"),
                  guidance="Significance, Innovation, Approach for each core element; NOFO may define its own outline."),
        Component("admin", "Administrative Capacity / Center structure", "narrative",
                  kb_keys=("org.leadership", "org.financials", "kata.summary"),
                  answers=("Administrative Capacity", "administrative infrastructure", "translation and dissemination")),
        Component("engagement", "Collaboration & Engagement plan (incl. Youth Advisory Council)", "narrative",
                  kb_keys=("org.partners",), answers=("Collaboration and Engagement", "partnerships", "youth advisory council")),
        Component("training", "Training & Education plan (early career researchers)", "narrative",
                  answers=("Training and Education", "early career researchers")),
        Component("bibliography", "Bibliography & References Cited", "attachment", kb_keys=("evidence",)),
        Component("facilities", "Facilities & Other Resources", "attachment", kb_keys=("kata.summary", "org.partners")),
        Component("equipment", "Equipment", "attachment"),
        Component("keypersons", "R&R Senior/Key Person Profiles + Biosketches", "form", kb_keys=("org.leadership",)),
        Component("budget", "R&R Budget + Budget Justification", "form", kb_keys=("org.financials",),
                  guidance="Annual detail; subaward budgets; F&A per negotiated rate or de minimis 15% MTDC."),
        Component("subaward", "R&R Subaward Budget Attachment(s)", "form", required=False),
        Component("human_subjects", "PHS Human Subjects & Clinical Trials Information", "form",
                  kb_keys=("program.safeguards",), answers=("youth aged",),
                  guidance="Minors -> 45 CFR 46 Subpart D; inclusion enrollment; protection of human subjects."),
        Component("dmsp", "Data Management and Sharing Plan", "attachment", kb_keys=("kata.data_use",)),
        Component("letters", "Letters of Support", "attachment", kb_keys=("org.partners",), answers=("partnerships",)),
        Component("sflll", "Disclosure of Lobbying Activities (SF-LLL)", "form", required=False),
        Component("assurances", "Assurances/Certifications (via SAM.gov registration)", "form"),
        # Applicant-type specific attachments
        Component("irs_letter", "IRS 501(c)(3) determination letter (if claimed)", "attachment", required=False,
                  kb_keys=("org.tax_status",), applies_to=("nonprofit",)),
        Component("board", "Governing board roster", "attachment", required=False, kb_keys=("org.board",), applies_to=("nonprofit",)),
        Component("audit", "Most recent audit / Single Audit status (2 CFR 200 Subpart F)", "attachment", required=False,
                  kb_keys=("org.financials.audit",), applies_to=("nonprofit",)),
        Component("no_fee", "Statement: no profit or fee charged (2 CFR 200.400(g))", "attachment",
                  kb_keys=("org.financials.statements",), applies_to=("for_profit",)),
        Component("fin_statements", "Financial statements (2 yrs) / financial capability", "attachment",
                  kb_keys=("org.financials.statements",), applies_to=("for_profit",)),
        Component("ownership", "Ownership / size status (SBA) disclosure", "attachment", required=False,
                  kb_keys=("org.ownership", "org.business_size"), applies_to=("for_profit",)),
    ),
)

SF424_STANDARD = Package(
    id="sf424",
    name="SF-424 standard (non-research) package",
    used_for="Program/service grants (SAMHSA, HRSA, DOJ/OJP, state pass-through)",
    components=(
        Component("sf424", "SF-424 Application for Federal Assistance", "form", kb_keys=("org.legal_name", "org.uei", "org.ein")),
        Component("sf424a", "SF-424A Budget Information (non-construction)", "form", kb_keys=("org.financials",)),
        Component("sf424b", "SF-424B Assurances (or via SAM)", "form"),
        Component("abstract", "Project Abstract Summary", "narrative", page_limit=1, kb_keys=("program.summary",)),
        Component("need", "Statement of Need", "narrative", answers=("need", "population", "higher than")),
        Component("approach", "Project Approach / Work Plan", "narrative", kb_keys=("program.summary",), answers=("approach", "should")),
        Component("evaluation", "Evaluation & Performance Measurement", "narrative", answers=("evaluation", "performance")),
        Component("capacity", "Organizational Capacity", "narrative", kb_keys=("org.leadership", "org.partners")),
        Component("budget_narr", "Budget Narrative/Justification", "attachment", kb_keys=("org.financials",)),
        Component("logic_model", "Logic Model", "attachment"),
        Component("letters", "Letters of Commitment", "attachment", kb_keys=("org.partners",)),
        Component("irs_letter", "IRS determination letter", "attachment", required=False, applies_to=("nonprofit",)),
        Component("no_fee", "No profit/fee statement", "attachment", applies_to=("for_profit",)),
    ),
)

PACKAGES = {p.id: p for p in (SF424_RR, SF424_STANDARD)}


def select_package(solicitation) -> Package:
    """Research RFAs use SF424 (R&R); everything else defaults to SF-424 standard."""
    return SF424_RR if getattr(solicitation, "is_research", False) else SF424_STANDARD
