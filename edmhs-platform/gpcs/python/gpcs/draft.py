"""Section drafter.

Two modes:
* ``template`` (default, offline, deterministic): fills each narrative component from KB facts and
  marks every unresolved item as [GAP: ...] so nothing is invented.
* ``claude`` (optional): sends the template draft, the solicitation requirements mapped to that
  component, and the KB facts to Claude for a polished draft. Claude is told to keep [GAP]/[DATA]
  markers rather than fabricate facts. Requires ANTHROPIC_API_KEY (or another SDK credential).
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from .crosswalk import Crosswalk, build_crosswalk
from .knowledge import KnowledgeBase
from .packages import select_package
from .solicitation import Solicitation

MODEL = "claude-opus-5-5"


@dataclass
class Section:
    component_id: str
    title: str
    requirements: list[str]
    text: str
    gaps: list[str]


def _fact(kb: KnowledgeBase, key: str, label: str | None = None) -> str:
    v = kb.get(key)
    if kb.has(key):
        if isinstance(v, list):
            v = "; ".join(x.get("name", str(x)) if isinstance(x, dict) else str(x) for x in v)
        elif isinstance(v, dict):
            v = json.dumps(v)
        return str(v).strip()
    return f"[GAP: {label or key}]"


def _template(cid: str, title: str, kb: KnowledgeBase, sol: Solicitation, reqs: list[str]) -> str:
    p = kb.program
    org = _fact(kb, "org.legal_name", "applicant legal name")
    ages = f"{sol.population_ages[0]}-{sol.population_ages[1]}" if sol.population_ages else "[GAP: ages]"
    zips = ", ".join((p.get("population") or {}).get("zip_codes", [])) or "[GAP: service area]"
    lines = [f"## {title}", ""]
    if cid == "abstract":
        lines += [f"{org} proposes {p.get('name')} for youth aged {ages} in ZIP codes {zips}. "
                  f"{p.get('summary', '').strip()}",
                  "Community context: [DATA: local youth violence rates vs. national average]."]
    elif cid in ("aims", "approach"):
        lines += ["Overall goal: reduce youth violence in the service area. [GAP: final aims after NOFO priority areas]"]
        lines += [f"- Addresses: {r}" for r in reqs]
    elif cid == "strategy":
        lines += ["### Significance", "[DATA: local burden vs. state and national]", "",
                  "### Approach", p.get("summary", "").strip(), ""]
        for band in p.get("developmental_bands", []):
            lines.append(f"- Ages {band['ages']}: {band['erikson']}; {band['piaget']}. Focus: {band['focus']}.")
        ev = [kb.evidence[k]["cite"] for k in p.get("evidence_keys", []) if k in kb.evidence]
        if ev:
            lines += ["", "Evidence base: " + " ".join(f"({c})" for c in ev)]
    elif cid in ("admin", "capacity"):
        lines += [f"Leadership: {_fact(kb, 'org.leadership', 'key personnel')}.",
                  f"Data infrastructure: {_fact(kb, 'kata.summary', 'records platform')}",
                  f"Indirect cost basis: {_fact(kb, 'org.financials.indirect_rate', 'indirect rate')}."]
    elif cid in ("engagement", "letters"):
        for partner in kb.get("org.partners") or []:
            lines.append(f"- {partner['name']}: {partner['role']} (letter: {partner.get('letter', 'pending')})")
        lines.append("Youth Advisory Council: [GAP: membership, meeting cadence, decision authority]")
    elif cid == "dmsp":
        lines += [_fact(kb, "kata.data_use", "data use and sharing approach")]
    elif cid == "human_subjects":
        lines += ["Population includes minors (45 CFR 46 Subpart D): guardian permission + youth assent."]
        lines += [f"- {s}" for s in p.get("safeguards", [])]
    elif cid == "bibliography":
        lines += [f"- {v['cite']}" + (" [VERIFY]" if v.get("verify") else "") for v in kb.evidence.values()]
    elif cid == "no_fee":
        lines += [f"{org} certifies that no profit or fee is included in this request (2 CFR 200.400(g))."]
    else:
        lines += [f"[GAP: draft {title}]"] + [f"- Must address: {r}" for r in reqs]
    return "\n".join(lines) + "\n"


def draft_sections(sol: Solicitation, kb: KnowledgeBase, mode: str = "template",
                   crosswalk: Crosswalk | None = None) -> list[Section]:
    cw = crosswalk or build_crosswalk(sol, kb)
    pkg = select_package(sol)
    sections = []
    for comp in pkg.for_applicant(kb.profile.applicant_type):
        if comp.kind == "form":
            continue
        reqs = [r.requirement for r in cw.rows if comp.id in r.components]
        text = _template(comp.id, comp.title, kb, sol, reqs)
        if mode == "claude":
            text = _claude_polish(comp.title, text, reqs, kb, comp.page_limit)
        gaps = sorted({seg.split("]")[0] for seg in text.split("[GAP: ")[1:]})
        sections.append(Section(comp.id, comp.title, reqs, text, gaps))
    return sections


def _claude_polish(title: str, draft: str, reqs: list[str], kb: KnowledgeBase, page_limit: float | None) -> str:
    import anthropic  # optional dependency

    client = anthropic.Anthropic()
    facts = {"organization": kb.profile.data, "program": kb.program, "evidence": kb.evidence}
    system = (
        "You draft sections of federal grant applications. Use only facts provided in <facts>. "
        "Where a needed fact is missing, keep or add a marker like [GAP: what is needed] or "
        "[DATA: statistic needed] instead of inventing it. Cite evidence only from the provided table. "
        "Write in clear, specific prose suited to federal reviewers; return Markdown only."
    )
    limit = f"Stay within about {page_limit} page(s) (~500 words/page)." if page_limit else ""
    user = (f"<facts>{json.dumps(facts, default=str)}</facts>\n<requirements>{json.dumps(reqs)}</requirements>\n"
            f"<template_draft>{draft}</template_draft>\nRewrite the section '{title}' so it answers every "
            f"requirement. {limit}")
    with client.messages.stream(model=MODEL, max_tokens=16000, thinking={"type": "adaptive"},
                                output_config={"effort": "high"}, system=system,
                                messages=[{"role": "user", "content": user}]) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        return draft + "\n<!-- Claude declined this section; template draft kept. -->\n"
    return "".join(b.text for b in msg.content if b.type == "text") or draft


def to_markdown(sections: list[Section], sol: Solicitation) -> str:
    head = f"# Draft application: {sol.opportunity_number} - {sol.title}\n\n"
    return head + "\n".join(s.text for s in sections)
