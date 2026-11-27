"""Build edmhs.org: static pages + literature rendered from ../docs Markdown.

usage: python site/build.py      (writes into site/edmhs-org/)
"""
from __future__ import annotations

import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "edmhs-org"
DOCS = ROOT.parent / "docs"

NAV = [("/", "Home"), ("/programs/", "Programs"), ("/programs/training-education.html", "Training & Education"),
       ("/literature/", "Literature"), ("/projects.html", "Projects"), ("/about.html", "About")]
APPS = [("https://ict.edmhs.us", "ICT"), ("https://kata.edmhs.us", "KATA")]
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">')


def page(title: str, path: str, body: str, desc: str) -> str:
    nav = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == path else ""}>{t}</a>' for h, t in NAV)
    apps = "".join(f'<a href="{h}">{t} ↗</a>' for h, t in APPS)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><meta name="description" content="{desc}">{FONTS}
<link rel="stylesheet" href="/assets/site.css"></head>
<body>
<header><div class="wrap"><a class="brand" href="/">EDMHS<span>.org</span></a><nav aria-label="Main">{nav}{apps}</nav></div></header>
<main>{body}</main>
<footer><div class="wrap">
<span>EDMHS.org · Empowered Disease Management Health Services · Toledo, Ohio</span>
<span><a href="https://ict.edmhs.us">Inner Combat Training</a> · <a href="https://kata.edmhs.us">KATA</a> · <a href="https://pmsg.edmhs.us">PMSG</a> · <a href="https://www.edmhs.us">EDM Health Services, LLC</a></span>
</div></footer>
</body></html>
"""


def render_md(src: Path) -> tuple[str, str]:
    text = src.read_text()
    title = re.search(r"^#\s+(.+)$", text, re.M).group(1)
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    return title, html


def write(rel: str, html: str) -> None:
    out = OUT / rel.lstrip("/")
    if rel.endswith("/"):
        out = out / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)


def main() -> None:
    for rel, (title, desc, body) in PAGES.items():
        write(rel, page(f"{title} | EDMHS.org", rel, body, desc))

    lit = [  # (slug, source markdown, blurb). Only items cleared for public release.
        ("youth-violence-prevention-white-paper", DOCS / "white-paper" / "youth_violence_prevention_white_paper.md",
         "What works to prevent youth violence, and how it applies to Toledo's 43607 / 43610 / 43620 corridor."),
    ]
    cards = []
    for slug, src, blurb in lit:
        title, html = render_md(src)
        write(f"/literature/{slug}.html", page(f"{title} | EDMHS.org", "/literature/",
              f'<div class="wrap"><article>{html}</article></div>', blurb))
        cards.append(f'<div class="card"><span class="tag">White paper · draft</span><h3>{title}</h3><p>{blurb}</p>'
                     f'<div class="go"><a class="btn" href="/literature/{slug}.html">Read</a></div></div>')
    cards.append('<div class="card"><span class="tag">Program manual</span><h3>PMSG technical manual</h3>'
                 '<p>Bookdown manual for the Pain Management Support Group outcomes platform.</p>'
                 '<div class="go"><a class="btn ghost" href="https://github.com/dah512/pmsg-platform/tree/main/manual">Source</a></div></div>')
    body = ('<div class="wrap hero"><p class="eyebrow">Literature</p><h1>Evidence we build on, and what we publish.</h1>'
            '<p class="lede">White papers, program manuals and research summaries from EDMHS programs. '
            'Drafts are labeled; citations are verified before final release.</p></div>'
            f'<section><div class="wrap grid">{"".join(cards)}</div></section>')
    write("/literature/", page("Literature | EDMHS.org", "/literature/", body,
                               "White papers and research summaries from EDMHS community programs."))
    print("built", sum(1 for _ in OUT.rglob("*.html")), "pages into", OUT)


PROGRAM_CARDS = """
<div class="card"><span class="tag ict">Youth violence prevention</span><h3>Inner Combat Training (ICT)</h3>
<p>Free martial arts and behavioral wellness for Toledo youth, taught to developmental stage. Every technique comes with the reason not to use it.</p>
<div class="go"><a class="btn" href="https://ict.edmhs.us">Open ict.edmhs.us</a><a class="btn ghost" href="https://ict.edmhs.us/enroll">Enroll</a></div></div>
<div class="card"><span class="tag">Platform · staff sign-in</span><h3>KATA</h3>
<p>Records and safety-workflow platform: role-restricted access, versioned consent, Ohio mandated-reporting workflow, de-identified analytics.</p>
<div class="go"><a class="btn" href="https://kata.edmhs.us">Open kata.edmhs.us</a></div></div>
<div class="card"><span class="tag">Training &amp; education</span><h3>Pain Management Support Group (PMSG)</h3>
<p>Eight-week, 32-session non-pharmacologic chronic pain program: pain neuroscience education, CBT, nutrition, Qi Gong and Tai Chi.</p>
<div class="go"><a class="btn" href="https://pmsg.edmhs.us">Open PMSG</a><a class="btn ghost" href="https://curriculum-pmsg.edmhs.us">Curriculum</a></div></div>
"""

PAGES = {
    "/": ("EDMHS.org", "Community-based, physician-led prevention and education in Toledo, Ohio.", f"""
<div class="wrap hero"><p class="eyebrow">Empowered Disease Management Health Services · Toledo, Ohio</p>
<h1>Community prevention, built where the need is.</h1>
<p class="lede">EDMHS.org is the community arm of EDMHS: physician-led programs for youth violence prevention, chronic pain self-management,
and privacy-preserving community health data, in the Junction, Englewood and Old West End neighborhoods and beyond.</p>
<p><a class="btn" href="https://ict.edmhs.us">Inner Combat Training ↗</a> <a class="btn ghost" href="https://kata.edmhs.us">KATA staff sign-in ↗</a></p></div>
<section class="band"><div class="wrap"><h2>Programs</h2><div class="grid">{PROGRAM_CARDS}</div></div></section>
<section><div class="wrap grid">
<div class="card"><span class="tag">Literature</span><h3>From the Corner Back to the Commons</h3><p>Our white paper on what works to prevent youth violence, and what it means for 43607, 43610 and 43620.</p><div class="go"><a class="btn" href="/literature/youth-violence-prevention-white-paper.html">Read the white paper</a></div></div>
<div class="card"><span class="tag">Projects</span><h3>ICT Youth Violence Prevention Center</h3><p>A proposed center to rigorously evaluate two community-designed approaches for youth aged 10 to 24.</p><div class="go"><a class="btn" href="/projects.html">See projects</a></div></div>
<div class="card"><span class="tag">Training &amp; education</span><h3>Learn with us</h3><p>Program curricula, facilitator training, peer-mentor credentials and early-career research training.</p><div class="go"><a class="btn" href="/programs/training-education.html">Training &amp; education</a></div></div>
</div></section>"""),
    "/programs/": ("Programs", "EDMHS community programs: ICT, KATA, PMSG.", f"""
<div class="wrap hero"><p class="eyebrow">Programs</p><h1>What we run.</h1>
<p class="lede">Each program has its own site. Navigation links here go to each program home, and each program links back to EDMHS.org.</p></div>
<section><div class="wrap grid">{PROGRAM_CARDS}</div></section>"""),
    "/programs/training-education.html": ("Training & Education", "Training and education programs at EDMHS.org.", """
<div class="wrap hero"><p class="eyebrow">Training &amp; education</p><h1>Skills that stay in the neighborhood.</h1>
<p class="lede">Curricula and training that build local capacity, for participants, families, facilitators and researchers.</p></div>
<section><div class="wrap grid">
<div class="card"><span class="tag">Chronic pain</span><h3>PMSG curriculum</h3><p>Eight weeks, 32 sessions: pain neuroscience education, CBT skills, anti-inflammatory nutrition, Qi Gong and Tai Chi movement, with BPI-SF and ODI outcome tracking.</p><div class="go"><a class="btn" href="https://curriculum-pmsg.edmhs.us">Curriculum hub</a><a class="btn ghost" href="https://pmsg.edmhs.us">Program site</a></div></div>
<div class="card"><span class="tag ict">Youth</span><h3>ICT curriculum</h3><p>Five-week first cycle, then six-week blocks. Traditional forms paired weekly with one behavioral skill: respect; breathe, then choose; handling frustration; self-control; confidence.</p><div class="go"><a class="btn" href="https://ict.edmhs.us/curriculum">Curriculum overview</a></div></div>
<div class="card"><span class="tag">Workforce</span><h3>Peer mentor &amp; facilitator credential</h3><p>A paid pathway for young adults aged 18 to 24 to become assistant instructors: de-escalation, trauma-informed practice, and knowing where teaching ends and clinical care begins.</p><div class="go"><span class="tag">In development</span></div></div>
<div class="card"><span class="tag">Research</span><h3>Early-career researcher training</h3><p>Community-engaged violence prevention research: causal inference for community trials, developmental science in program design, data ethics with minors, and reproducible R and Python workflows.</p><div class="go"><span class="tag">Planned with the ICT-YVPC</span></div></div>
</div></section>"""),
    "/projects.html": ("Projects", "Current EDMHS projects.", """
<div class="wrap hero"><p class="eyebrow">Projects</p><h1>Work in progress.</h1></div>
<section><div class="wrap grid">
<div class="card"><span class="tag ict">Proposal in preparation</span><h3>ICT Youth Violence Prevention Center</h3><p>Proposed for CDC's National Centers of Excellence in Youth Violence Prevention (RFA-CE-27-013). Approach A: Inner Combat Training, evaluated by randomized waitlist-controlled trial. Approach B: Corner-to-Commons, supervised after-school space with food and credible-messenger outreach, evaluated by stepped-wedge rollout. Youth Advisory Councils in each community.</p></div>
<div class="card"><span class="tag">Platform</span><h3>KATA + ICT shared backend</h3><p>PostgreSQL with six role-restricted views, versioned consent, mandated-reporting workflow, ICT↔KATA data-sharing grants, and analytics only on de-identified views.</p><div class="go"><a class="btn ghost" href="https://kata.edmhs.us">KATA</a></div></div>
<div class="card"><span class="tag">Tooling</span><h3>Grant Proposal Creation System (GPCS)</h3><p>Reads a funding solicitation, maps every requirement to the standard application package, and drafts sections from our knowledge base, with nonprofit and for-profit applicant profiles. Python and R engines.</p></div>
<div class="card"><span class="tag">Engineering</span><h3>NABS</h3><p>Non-Ambulatory Bathing System: drawing register, thermal simulator and operator console.</p><div class="go"><a class="btn ghost" href="https://nabs.edmhs.us">nabs.edmhs.us</a></div></div>
<div class="card"><span class="tag">Research</span><h3>Graphic GeoCode converter</h3><p>Address-to-geocode conversion for mapping substance use and treatment patterns at the community level, with privacy safeguards built in from the start.</p><div class="go"><span class="tag">In development</span></div></div>
</div></section>"""),
    "/about.html": ("About", "About EDMHS.org.", """
<div class="wrap hero"><p class="eyebrow">About</p><h1>Physician-led. Community-rooted.</h1>
<p class="lede">EDMHS.org grew out of Inner Combat Training, a community project with Soul City Wrestling and Boxing Clubs serving the neighborhoods where the Neighborhood Health Association was founded.</p></div>
<section><div class="wrap"><article>
<h2>Founder</h2>
<p><strong>Darrell A. Hall, MD, MSCIS</strong> is a residency-trained family physician with fourteen years of community practice, an MS in Computer Information Systems from Boston University, and certification as a Professional Data Scientist. He served as a U.S. Air Force communications-electronics officer in Europe during the move to packet-switched defense networks, and has trained in martial arts for fifty years.</p>
<h2>Contact</h2>
<p>Email <a href="mailto:dah512@edmhs.us">dah512@edmhs.us</a> · (419) 460-5695</p>
</article></div></section>"""),
}

if __name__ == "__main__":
    main()
