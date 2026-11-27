from pathlib import Path

import pytest

from gpcs import KnowledgeBase, build_crosswalk, parse
from gpcs.applicant import ForProfitProfile, NonprofitProfile
from gpcs.draft import draft_sections

HERE = Path(__file__).parent
PDF = HERE / "fixtures" / "RFA-CE-27-013_forecast.pdf"
KB = HERE.parents[2] / "knowledge_base"


@pytest.fixture(scope="module")
def sol():
    return parse(PDF)


def test_core_fields(sol):
    assert sol.opportunity_number == "RFA-CE-27-013"
    assert sol.agency.startswith("Centers for Disease Control")
    assert sol.award_ceiling == 1_200_000 and sol.award_floor == 0
    assert sol.total_funding == 30_000_000 and sol.expected_awards == 5
    assert sol.cost_sharing is False
    assert sol.instrument == "Cooperative agreement"
    assert sol.dates["due"] == "February 1, 2027"
    assert sol.dates["start"] == "September 30, 2027"
    assert sol.status == "forecasted"
    assert sol.population_ages == (10, 24)
    assert sol.implied_years == 5.0
    assert sol.is_research
    assert "ncipc_erpo@cdc.gov" in sol.contacts
    assert sol.assistance_listings[0].startswith("93.136")
    assert sol.missing == []


def test_core_elements_and_eligibility(sol):
    names = [c.name for c in sol.core_elements]
    assert names == ["Administrative Capacity", "Research and Rigorous Evaluation",
                     "Collaboration and Engagement", "Training and Education"]
    assert {"nonprofit", "for_profit", "government", "education"} <= sol.eligible_groups
    assert sol.eligible_for("nonprofit") and sol.eligible_for("for_profit")
    assert any("youth advisory council" in r.lower() for r in sol.requirements)


@pytest.mark.parametrize("org,cls", [("edmhs_org", NonprofitProfile), ("edm_health_services_llc", ForProfitProfile)])
def test_profiles_and_crosswalk(sol, org, cls):
    kb = KnowledgeBase.load(KB, org, "ict")
    assert isinstance(kb.profile, cls)
    cw = build_crosswalk(sol, kb)
    assert cw.eligible
    ce_rows = [r for r in cw.rows if r.source == "core_element"]
    assert len(ce_rows) == 4 and all(r.components for r in ce_rows)
    assert any("Population mismatch" in f for f in cw.flags)
    assert any("per budget year" in f for f in cw.flags)
    md = cw.to_markdown()
    assert "Compliance crosswalk" in md
    if org == "edmhs_org":
        assert any("uei" in f for f in cw.flags)          # nonprofit not yet in SAM
        assert "irs_letter" in cw.component_status and "no_fee" not in cw.component_status
    else:
        assert any("profit/fee" in f for f in cw.flags)
        assert "no_fee" in cw.component_status and "irs_letter" not in cw.component_status


def test_draft_template_marks_gaps(sol):
    kb = KnowledgeBase.load(KB, "edmhs_org", "ict")
    secs = {s.component_id: s for s in draft_sections(sol, kb)}
    assert "strategy" in secs and "Industry vs. inferiority" in secs["strategy"].text
    assert secs["abstract"].text.count("[DATA") >= 1
    assert all(s.component_id not in {"sf424_rr", "budget"} for s in secs.values())
