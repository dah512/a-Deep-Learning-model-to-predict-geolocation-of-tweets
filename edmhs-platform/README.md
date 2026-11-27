# EDMHS platform

The ICT Youth Violence Prevention Center proposal, the **Grant Proposal Creation System (GPCS)**, and **edmhs.org** with the shared PostgreSQL backend for `ict.edmhs.us` and `kata.edmhs.us`.

> **Staging location.** This folder lives temporarily in the `a-Deep-Learning-model-to-predict-geolocation-of-tweets` repository because the session that built it could not create a new repository. Move it to its own repository (suggested name: `edmhs-org`) by copying `edmhs-platform/` to the new repo's root and moving `.github/workflows/edmhs-platform-ci.yml` to the new repo's `.github/workflows/` (drop its `working-directory` default).

## What's here

| Path | What | Status |
|---|---|---|
| `docs/proposal/ICT_YVPC_RFA-CE-27-013_draft.md` | Draft proposal for CDC RFA-CE-27-013 (YVPCs) | Draft v0.1, written to the forecast; revise when the NOFO posts Dec 1, 2026 |
| `docs/proposal/crosswalk_*.md` | GPCS compliance crosswalks, nonprofit vs. for-profit applicant | Generated |
| `docs/proposal/gpcs_template_draft.md` | GPCS auto-draft from the knowledge base (shows gaps) | Generated |
| `docs/planning/milestones_and_critical_path.md` | Milestones, critical paths (Mermaid) for proposal, GPCS and site, plus interconnects and Gantt | v0.1 |
| `docs/white-paper/youth_violence_prevention_white_paper.md` | *From the Corner Back to the Commons*: evidence review | Draft; verify citations |
| `knowledge_base/` | YAML facts GPCS drafts from: organizations (nonprofit and for-profit), programs, evidence | Fill in `TODO`s |
| `gpcs/python/` | GPCS Python engine: parser, package templates, applicant profiles, crosswalk, drafter (optional Claude), CLI, FastAPI | 5 tests pass |
| `gpcs/r/` | GPCS R engine (same logic), plumber API | 22 tests pass |
| `db/init/` | PostgreSQL 16 schema: intake, versioned consent, safety (ORC 2151.421), ICT↔KATA collaboration grants, research, de-identified analytics, grants, audit; six roles plus row-level security | 8 role-isolation tests pass |
| `db/dev/` | Synthetic participants, for **dev/test only** | |
| `services/api/` | EDMHS API: ICT enrollment (encrypted PII), analytics with small-cell suppression, GPCS mounted at `/gpcs` | 8 integration tests pass |
| `web/react/` | Grant Studio UI → Python engine | Builds |
| `web/angular/` | Grant Studio UI → R engine | Builds |
| `site/` | edmhs.org static site (built from `docs/` Markdown), with navigation to and from ICT and KATA | 7 pages |

## Run it

```bash
cp .env.example .env          # set the passwords and PII_KEY
docker compose up --build
```

| URL | Service |
|---|---|
| http://localhost:8080 | edmhs.org |
| http://localhost:5173 | Grant Studio (React → Python) |
| http://localhost:4200 | Grant Studio (Angular → R) |
| http://localhost:8000/docs | EDMHS API (intake + `/gpcs`) |
| http://localhost:8001/__docs__/ | GPCS R API |

## GPCS from the command line

```bash
cd edmhs-platform
PYTHONPATH=gpcs/python python -m gpcs.cli analyze path/to/NOFO.pdf
PYTHONPATH=gpcs/python python -m gpcs.cli intake nonprofit           # or for_profit
PYTHONPATH=gpcs/python python -m gpcs.cli crosswalk NOFO.pdf --org edmhs_org --program ict
PYTHONPATH=gpcs/python python -m gpcs.cli draft NOFO.pdf --org edmhs_org --program ict --mode template
# --mode claude polishes each section with Claude (needs ANTHROPIC_API_KEY); [GAP]/[DATA] markers are kept, never invented
```

In R:

```r
for (f in list.files("gpcs/r/R", full.names = TRUE)) source(f)
sol <- parse_solicitation("NOFO.pdf")
cw  <- build_crosswalk(sol, load_kb("knowledge_base", "edmhs_org", "ict"))
cat(crosswalk_markdown(cw))
```

### How GPCS works
1. **Parse** the solicitation (Grants.gov listing, forecast or full NOFO) into structured fields: dates, ceiling, awards, eligibility, population, core elements and requirement sentences. Missing fields are reported in `missing`, never guessed.
2. **Select the package**: SF424 (R&R) for research RFAs/PAs, SF-424 standard otherwise.
3. **Load the applicant profile**. `NonprofitProfile` asks for the 501(c)(3) letter, board and Single Audit status. `ForProfitProfile` asks for SBA size, NAICS, ownership and financial statements, and enforces the no-fee rule. Each profile lists the federal rules that apply to it.
4. **Crosswalk**: every requirement → package component → knowledge-base facts, with statuses `facts available`, `partial`, `gap`, `needs narrative` or `blocker`. It also raises flags such as a population mismatch, a per-year ceiling or a SAM.gov blocker.
5. **Draft** each narrative section from the knowledge base, with optional Claude polishing.

## Tests

```bash
PYTHONPATH=gpcs/python pytest -q gpcs/python/tests
(cd gpcs/r/tests && Rscript testthat.R)
PGHOST=... PGUSER=postgres db/tests/test_access.sh
(cd services/api && INTAKE_DATABASE_URL=... ANALYTICS_DATABASE_URL=... PII_KEY=... PYTHONPATH=.:../../gpcs/python pytest -q tests)
```

## Privacy notes
- Phone and health fields are encrypted with `pgp_sym_encrypt`. The key is supplied by the app (`PII_KEY`) and never stored in the database.
- The analyst role can read only `analytics.*` views, which are keyed by an HMAC research ID whose salt the analyst cannot read.
- Facilitators see only their own cohorts. Clinicians (KATA) see only participants covered by an active `collab.access_grant`.
- Consent rows reference the exact `consent_version` text shown (SHA-256 stored).
- The enrollment API never echoes identifiers back to the browser.
