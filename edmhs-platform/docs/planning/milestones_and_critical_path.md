# Milestones and critical paths

Today: **2026-11-27**. Hard deadline: **CDC RFA-CE-27-013 due 2027-02-01** (forecast). Three workstreams:

- **P**: Proposal (draft → submission)
- **G**: Grant Proposal Creation System (GPCS)
- **W**: edmhs.org site, plus the shared Postgres backend for ict.edmhs.us and kata.edmhs.us

On the diagrams, a ★ or a red node marks the critical path. Any slip on it moves the submission date.

---

## 1. Proposal critical path (P)

The longest chain is **entity registration → Grants.gov/eRA accounts → validated submission**. Writing is *not* the critical path; registration and partner letters are.

```mermaid
flowchart LR
  classDef crit fill:#8c2b42,color:#fff,stroke:#6b1f31
  P0[P0 Decide applicant entity<br/>by Dec 1]:::crit --> P1[P1 SAM.gov UEI registration<br/>Dec 1 → ≤ Jan 9]:::crit
  P1 --> P2[P2 Grants.gov EBiz POC + AOR<br/>≤ Jan 14]:::crit
  P1 --> P3[P3 eRA Commons institution + PD/PI<br/>≤ Jan 16]:::crit
  N0[NOFO posts Dec 1] --> N1[N1 Parse NOFO in GPCS<br/>priority areas, page limits, criteria<br/>Dec 2–3]
  N1 --> W1[W1 Revise aims + approaches<br/>to priority areas Dec 4–12]
  U0[U0 University evaluation partner<br/>commitment ≤ Jan 5]:::crit --> W2[W2 Research strategy + power + ECR plan<br/>Dec 13 – Jan 9]
  W1 --> W2
  L0[L0 Request letters: NHA, Soul City,<br/>TPS, City, TPD Dec 5] --> L1[L1 Letters signed ≤ Jan 16]:::crit
  D0[D0 Epi data pull: Lucas vs OH vs US<br/>Dec 8–19] --> W3[W3 Background + significance Dec 20–Jan 2]
  W2 --> B1[B1 Budget + justification + subaward budgets<br/>Jan 5–14]
  U0 --> B1
  W2 & W3 & B1 & L1 --> A1[A1 Assemble SF424 R&R package<br/>Jan 15–20]:::crit
  P2 & P3 --> A1
  A1 --> A2[A2 Internal red-team review Jan 21–24]:::crit
  A2 --> A3[A3 Submit + validate in eRA<br/>target Jan 27, 5 days of buffer]:::crit
  A3 --> A4((Due Feb 1)):::crit
```

### Proposal milestones
| ID | Milestone | Owner | Due | Done when |
|---|---|---|---|---|
| P-M1 | Applicant entity decided (Option A/B/C) | Dr. Hall | **2026-12-01** | Written decision; SAM registration started |
| P-M2 | NOFO parsed; compliance matrix generated (GPCS) | GPCS | 2026-12-03 | Every NOFO requirement mapped to a section |
| P-M3 | University evaluation partner committed | Dr. Hall | **2027-01-05** | Signed letter of intent + named co-I |
| P-M4 | Specific Aims page final | PI + co-I | 2026-12-12 | Red-team reviewed |
| P-M5 | Epidemiology section with Lucas/OH/US comparisons | Data | 2027-01-02 | All [DATA] tags resolved |
| P-M6 | SAM active; Grants.gov + eRA roles active | Admin | **2027-01-16** | Test login + AOR confirmed |
| P-M7 | All letters of support received | Engagement | **2027-01-16** | PDFs in package |
| P-M8 | Budget and subaward budgets final | Admin | 2027-01-14 | Ties to ≤ $1.2M |
| P-M9 | Package assembled; red-team complete | All | 2027-01-24 | Score ≥ "Excellent" on mock review |
| P-M10 | Submitted and validated | AOR | **2027-01-27** | eRA Commons shows no errors |

---

## 2. GPCS critical path (G)

```mermaid
flowchart LR
  classDef crit fill:#8c2b42,color:#fff,stroke:#6b1f31
  G1[G1 Solicitation parser<br/>PDF/text → structured]:::crit --> G2[G2 Package templates<br/>SF424 R&R, SF424 std]:::crit
  G2 --> G3[G3 Applicant profiles<br/>nonprofit vs for-profit]:::crit
  G3 --> G4[G4 Knowledge base YAML<br/>org, programs, evidence]
  G1 & G2 & G4 --> G5[G5 Crosswalk / compliance matrix]:::crit
  G5 --> G6[G6 Section drafter<br/>template + optional Claude]:::crit
  G6 --> G7[G7 FastAPI + React UI]
  G6 --> G8[G8 R mirror + plumber + Angular UI]
  G7 & G8 --> G9[G9 Grants.gov opportunity search<br/>XML extract / API]
  G9 --> G10[G10 Pipeline: many proposals]
```

| ID | Milestone | Due | Done when |
|---|---|---|---|
| G-M1 | Parser, templates, profiles, crosswalk working, tested in Python and R | **2026-11-30** (this session: v0.1) | `pytest` and `testthat` pass on RFA-CE-27-013 |
| G-M2 | Parses full NOFO PDF (posted Dec 1) | 2026-12-03 | Page limits, criteria and priority areas extracted |
| G-M3 | Drafter produces every SF424 R&R narrative section from the KB | 2026-12-10 | Section stubs with gap list |
| G-M4 | React UI (Python) and Angular UI (R) hit parity | 2026-12-20 | Same crosswalk output from both stacks |
| G-M5 | Grants.gov search and ingest (Search2 API / XML extract) | 2027-01-31 | Daily matched-opportunity feed |
| G-M6 | Second proposal generated end-to-end (e.g. SAMHSA, OCJS, HRSA) | 2027-03-15 | Submitted or in review |

---

## 3. edmhs.org + shared backend critical path (W)

```mermaid
flowchart LR
  classDef crit fill:#8c2b42,color:#fff,stroke:#6b1f31
  W1[W1 Postgres schema<br/>intake, consent, roles,<br/>collab ICT↔KATA, grants]:::crit --> W2[W2 Intake API<br/>FastAPI + plumber]:::crit
  W2 --> W3[W3 ICT enroll form → API<br/>replace 'preview only' form]:::crit
  W0[W0 edmhs.org static site<br/>home, programs, T&E, literature,<br/>projects, grants] --> W4[W4 Cross-nav buttons<br/>edmhs.org ⇄ ict ⇄ kata]
  W4 --> W5[W5 Deploy edmhs.org<br/>Firebase hosting + DNS]
  W3 --> W6[W6 Security review: RLS, pgcrypto,<br/>consent versioning, audit log]:::crit
  W6 --> W7[W7 Go-live intake<br/>before YVPC recruitment]:::crit
  W5 --> W8[W8 Literature: white paper,<br/>proposal summary, PMSG]
```

| ID | Milestone | Due | Done when |
|---|---|---|---|
| W-M1 | Schema + seed run on Postgres 16 | **2026-11-30** (v0.1) | `psql -f` clean; RLS policies on |
| W-M2 | edmhs.org pages built with nav to and from ICT and KATA | 2026-11-30 (v0.1) | Static site served by container |
| W-M3 | edmhs.org deployed and DNS live | 2026-12-10 | https://edmhs.org resolves |
| W-M4 | ICT enroll form posts to the intake API (consent workflow on) | 2027-01-15 | End-to-end test with synthetic child |
| W-M5 | Security review + penetration test | 2027-03-01 | Findings closed |
| W-M6 | Intake live for YVPC recruitment | 2027-09-30 | Matches award start |

---

## 4. Inter-connection points

These are tasks where one workstream blocks another. They are the places to watch.

```mermaid
flowchart TB
  classDef crit fill:#8c2b42,color:#fff,stroke:#6b1f31
  subgraph P[Proposal]
    PA[Aims + approaches]
    PB[Data mgmt + sharing plan]
    PC[Facilities & resources]
    PD[Submission]:::crit
  end
  subgraph G[GPCS]
    GA[NOFO parser]:::crit
    GB[Compliance matrix]:::crit
    GC[Section drafter]
  end
  subgraph W[edmhs.org + backend]
    WA[Postgres schema + RLS]
    WB[edmhs.org live]
    WC[Literature hub]
  end
  GA -->|X1 NOFO requirements Dec 3| PA
  GB -->|X2 gap list drives writing| PA
  WA -->|X3 schema = data dictionary for DMS plan| PB
  WA -->|X4 KATA capability evidence| PC
  WB -->|X5 public URL cited in proposal| PD
  PA -->|X6 proposal text seeds KB| GC
  PD -->|X7 white paper + abstract published| WC
```

| ID | Interconnect | From → To | Needed by |
|---|---|---|---|
| X1 | NOFO requirements extracted | GPCS → Proposal | 2026-12-03 |
| X2 | Compliance and gap matrix | GPCS → Proposal | Weekly from Dec 4 |
| X3 | Schema data dictionary → Data Management & Sharing Plan | Backend → Proposal | 2027-01-09 |
| X4 | KATA/ICT platform demo → Facilities & Resources | Backend → Proposal | 2027-01-09 |
| X5 | edmhs.org live (credibility, public program page) | Site → Proposal | 2027-01-15 |
| X6 | Final proposal text → knowledge base for future proposals | Proposal → GPCS | 2027-02-01 |
| X7 | White paper + abstract → literature hub | Proposal → Site | 2027-02-05 |

## 5. Gantt (all workstreams)

```mermaid
gantt
  dateFormat YYYY-MM-DD
  title ICT-YVPC submission: Nov 2026 → Feb 2027
  section Proposal
  Applicant decision            :crit, p0, 2026-11-27, 2026-12-01
  SAM / Grants.gov / eRA        :crit, p1, 2026-12-01, 2027-01-16
  NOFO analysis                 :p2, 2026-12-01, 3d
  Aims + approaches             :p3, after p2, 9d
  Partner letters               :crit, p4, 2026-12-05, 2027-01-16
  Epi data (Claude Science)     :p5, 2026-12-08, 2027-01-02
  Research strategy             :p6, 2026-12-13, 2027-01-09
  Budget                        :p7, 2027-01-05, 2027-01-14
  Assemble + red team           :crit, p8, 2027-01-15, 2027-01-24
  Submit + validate             :crit, milestone, p9, 2027-01-27, 0d
  section GPCS
  v0.1 core (parser→crosswalk)  :g1, 2026-11-27, 4d
  Full NOFO ingest              :g2, 2026-12-01, 3d
  Drafter + UIs                 :g3, 2026-12-04, 2026-12-20
  Grants.gov feed               :g4, 2027-01-02, 2027-01-31
  section edmhs.org + backend
  Schema + site v0.1            :w1, 2026-11-27, 4d
  Deploy edmhs.org              :w2, 2026-12-01, 2026-12-10
  Intake API + ICT form         :w3, 2026-12-10, 2027-01-15
  Security review               :w4, 2027-01-15, 2027-03-01
```
