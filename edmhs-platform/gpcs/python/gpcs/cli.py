"""Command line: gpcs analyze | crosswalk | intake | draft."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .applicant import PROFILE_CLASSES
from .crosswalk import build_crosswalk
from .draft import draft_sections, to_markdown
from .knowledge import KnowledgeBase
from .solicitation import parse


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="gpcs", description="Grant Proposal Creation System")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("analyze", help="parse a solicitation to JSON")
    a.add_argument("solicitation")
    for name in ("crosswalk", "draft"):
        p = sub.add_parser(name)
        p.add_argument("solicitation")
        p.add_argument("--kb", default="knowledge_base")
        p.add_argument("--org", required=True)
        p.add_argument("--program", required=True)
        p.add_argument("-o", "--out")
        if name == "draft":
            p.add_argument("--mode", choices=["template", "claude"], default="template")
    i = sub.add_parser("intake", help="print intake questions for an applicant type")
    i.add_argument("type", choices=sorted(PROFILE_CLASSES))
    args = ap.parse_args(argv)

    if args.cmd == "analyze":
        out = json.dumps(parse(args.solicitation).to_dict(), indent=2, default=str)
    elif args.cmd == "intake":
        cls = PROFILE_CLASSES[args.type]
        out = json.dumps({"applicant_type": args.type, "rules": cls.rules,
                          "questions": [q.__dict__ for q in cls.questions]}, indent=2)
    else:
        sol = parse(args.solicitation)
        kb = KnowledgeBase.load(args.kb, args.org, args.program)
        if args.cmd == "crosswalk":
            out = build_crosswalk(sol, kb).to_markdown()
        else:
            out = to_markdown(draft_sections(sol, kb, mode=args.mode), sol)
    if getattr(args, "out", None):
        Path(args.out).write_text(out)
    else:
        sys.stdout.write(out + ("\n" if not out.endswith("\n") else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
