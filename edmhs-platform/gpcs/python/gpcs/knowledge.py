"""Knowledge base: organization profile + program files + evidence, addressable by dotted keys.

Key namespaces: ``org.*`` (applicant), ``program.*`` (the program being proposed),
``<program_id>.*`` (any other program, e.g. ``kata.data_use``), ``evidence`` (citation table).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .applicant import ApplicantProfile, load_profile


@dataclass
class KnowledgeBase:
    profile: ApplicantProfile
    programs: dict[str, dict]
    evidence: dict[str, dict]
    program_id: str

    @classmethod
    def load(cls, root: str | Path, org: str, program: str) -> "KnowledgeBase":
        root = Path(root)
        profile = load_profile(root / "organizations" / f"{org}.yaml")
        programs = {p.stem: yaml.safe_load(p.read_text()) for p in (root / "programs").glob("*.yaml")}
        ev_path = root / "evidence.yaml"
        evidence = yaml.safe_load(ev_path.read_text()) if ev_path.exists() else {}
        if program not in programs:
            raise KeyError(f"program {program!r} not in {sorted(programs)}")
        return cls(profile, programs, evidence, program)

    @property
    def program(self) -> dict:
        return self.programs[self.program_id]

    def get(self, key: str) -> Any:
        head, _, rest = key.partition(".")
        if head == "org":
            return self.profile.get(rest)
        if head == "evidence":
            return self.evidence
        src = self.program if head == "program" else self.programs.get(head)
        if src is None:
            return None
        cur: Any = src
        for part in rest.split(".") if rest else []:
            if not isinstance(cur, dict):
                return None
            cur = cur.get(part)
        return cur

    def has(self, key: str) -> bool:
        return not ApplicantProfile._is_blank(self.get(key))
