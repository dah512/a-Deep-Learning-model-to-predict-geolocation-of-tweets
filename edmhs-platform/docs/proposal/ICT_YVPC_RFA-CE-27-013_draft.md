# Inner Combat Training Youth Violence Prevention Center (ICT-YVPC)
## Draft proposal: CDC RFA-CE-27-013, National Centers of Excellence in Youth Violence Prevention

| Field | Value |
|---|---|
| Funding opportunity | RFA-CE-27-013, *CDC National Centers of Excellence in Youth Violence Prevention (YVPCs): Rigorous Evaluation of Prevention Approaches to Prevent and Reduce Youth Violence* |
| Assistance listing | 93.136, Injury Prevention and Control Research and State and Community Based Programs |
| Instrument | Cooperative agreement (substantial CDC involvement) |
| Ceiling | $1,200,000 per award. $30M ÷ 5 expected awards = $6M each, which implies **five budget years at ≈$1.2M/year** (confirm against the NOFO when it posts) |
| Cost share | None required |
| Key dates (forecast) | NOFO posts **Dec 1, 2026** · Application due **Feb 1, 2027** · Award **Aug 28, 2027** · Start **Sep 30, 2027** |
| Applicant | **EDMHS.org** (nonprofit; decided 2026-11-27; Ohio incorporation in progress). EDM Health Services, LLC participates only as an at-cost technology vendor/subrecipient under a conflict-of-interest plan. See §0 and `docs/entity/edmhs_org_formation_plan.md` |
| Program Director/PI (proposed) | Darrell A. Hall, MD, MSCIS |
| Target population | Youth aged **10–24** in Toledo ZIP codes 43607, 43610 and 43620 (Junction, Englewood, Old West End and adjacent neighborhoods), Lucas County, Ohio |
| Status | **DRAFT v0.1, 2026-11-27.** Written against the forecast summary. The full NOFO (priority research areas, page limits, scoring criteria) is due Dec 1, 2026. Every section marked ⚠ must be revised against it. |

> Conventions: **[DATA: …]** marks a number to be pulled in the epidemiology phase (Lucas County vs. Ohio vs. U.S.). **[CONFIRM: …]** marks a fact or partner commitment the applicant must verify before submission. **[NOFO]** marks text that depends on the full announcement.

---

## 0. Decisions required before writing further (critical path)

1. **Applicant entity.** The forecast lists nonprofits with or without 501(c)(3) status, small businesses and for-profits as eligible, so either EDMHS entity can apply.
   - *Option A, EDMHS.org nonprofit as applicant (preferred for community origin).* It requires an active SAM.gov registration with its own UEI, a Grants.gov organizational account (E-Business Point of Contact) and an eRA Commons institutional account. **SAM registration commonly takes 2–6 weeks.** It must start the week of Dec 1, 2026, or this option fails the Feb 1 deadline.
   - *Option B, EDM Health Services, LLC as applicant.* SAM UEI FSMJREGJGPJ3 and CAGE 91US7 are already on file. Under 2 CFR 200.400(g) and 45 CFR 75.216 a for-profit recipient may earn no profit or fee on the award. EDMHS.org then participates as the community partner and subrecipient.
   - *Option C, university applicant (UToledo or BGSU) with EDMHS as subrecipient.* It is the most competitive for the **early-career researcher training** core element and for IRB capacity. EDMHS keeps program ownership through the subaward.
   - **DECIDED 2026-11-27: Option A (EDMHS.org).** 501(c)(3) status is not required (nonprofits without 501(c)(3) are eligible). **Fallback trigger:** if SAM.gov has not activated the nonprofit by **Jan 12, 2027**, submit under Option B or C with EDMHS.org as the named community partner. Under any option, secure a university partner as the evaluation and training co-lead (see §6).
2. **Age range.** ICT currently serves ages 6–16. The NOFO population is **10–24**. ICT-YVPC extends ICT upward with a tiered pathway: 10–14 participants, 15–17 junior leaders, and 18–24 paid peer mentors and assistant instructors. Ages 6–9 continue on other funding and are not counted in YVPC outcomes.
3. **Two distinct approaches** are required, each mapped to ≥2 NOFO priority research areas [NOFO]. They are proposed below as **Approach A (ICT, individual and relationship level)** and **Approach B (Corner-to-Commons, community level)**.

---

## 1. Project summary / abstract (≤30 lines) ⚠

The ICT Youth Violence Prevention Center (ICT-YVPC) will rigorously evaluate two distinct, community-designed approaches to reduce violence among youth aged 10–24 in three Toledo, Ohio ZIP codes (43607, 43610, 43620). These are federally designated health professional shortage areas where youth violence exceeds the national average [DATA: assault-injury ED visits, youth homicide and juvenile violent-offense rates vs. U.S.]. A mass shooting at the Old West End Festival [CONFIRM: date and casualties] grew out of a dispute between two armed young men from the surrounding neighborhoods. It made visible what residents already knew: young people here have too few supervised places to be, too little to eat, and too few adults who stay.

**Approach A, Inner Combat Training (ICT),** is a developmentally staged program that pairs traditional martial arts (Tae Kwon Do, Shorin-Ryu, Kung Fu, Qi Gong) with structured social-emotional skill practice. Instruction is keyed to Erikson's psychosocial stages and Piaget's cognitive stages rather than to age alone, and older youth (18–24) are employed as peer mentors. **Approach B, Corner-to-Commons,** is a place-based, community-level intervention. It converts the out-of-school hours that youth now spend on street corners, after exclusion from fast-food restaurants, into supervised "commons" time with food, credible-messenger outreach and youth-run activity.

Approach A is evaluated by an individually randomized waitlist-controlled trial (target N=360). Approach B is evaluated by a stepped-wedge rollout across eight micro-sites with comparative interrupted time series and synthetic-control analysis of police calls for service, assault-injury ED visits and school discipline.

The Center will build administrative and data infrastructure on KATA, a role-restricted, de-identifying PostgreSQL records platform. It will establish a Youth Advisory Council in each intervention community, partner with the Neighborhood Health Association (NHA), Soul City Wrestling and Boxing Clubs, Toledo Public Schools and [university partner], and train [n] early-career researchers per year.

---

## 2. Specific aims (1 page) ⚠

**Overall goal:** reduce physical fighting, bullying perpetration and victimization, weapon carrying, and violence-related injury among youth aged 10–24 in Toledo's 43607/43610/43620 corridor, and produce transferable evidence for comparable under-resourced urban communities.

- **Aim 1 (Approach A):** Test whether ICT reduces self-reported physical fighting, bullying perpetration and weapon carrying, and improves emotion regulation, compared with waitlist control at 6 and 12 months.
  - *H1a:* ICT participants report ≥25% fewer fighting episodes at 12 months.
  - *H1b:* Effects are mediated by gains in self-regulation and in perceived adult connectedness.
  - *H1c:* Effects are moderated by developmental stage (Erikson and Piaget band), not chronological age alone.
- **Aim 2 (Approach B):** Test whether Corner-to-Commons reduces youth-involved violent incidents and assault-related injuries in treated micro-areas compared with synthetic controls.
  - *H2:* Calls for service involving youth disturbance, fights or assaults decline ≥15% within 400 m of activated commons sites during operating hours, without displacement to adjacent blocks.
- **Aim 3 (Mechanisms and equity):** Quantify the contribution of food insecurity, Medicaid-indexed poverty and out-of-school unsupervised time to violence risk, and whether each approach attenuates it.
- **Aim 4 (Translation):** Produce implementation guides, fidelity tools and an open de-identified analytic dataset, and disseminate them with CDC and the YVPC network.

---

## 3. Background and significance ⚠

### 3.1 The problem in this place
- Lucas County / Toledo youth violence indicators vs. Ohio and U.S. [DATA: CDC WISQARS, Ohio Dept. of Health, Ohio YRBS, Lucas County Juvenile Court, Toledo Police Department calls for service, ProMedica and Mercy ED assault visits].
- The 43607/43610/43620 corridor is a **health professional shortage area** with few private practices. Community clinics, chiefly the **Neighborhood Health Association (NHA)**, founded in the Junction, Englewood and Old West End neighborhoods, carry the primary-care and school-based care load. [DATA: Medicaid enrollment share among ages 10–24; child poverty rate; SNAP participation; HRSA HPSA scores].
- **Observed pattern:** youth congregated at a nearby fast-food restaurant after school because they were hungry and had nowhere else to go. Behavior escalated and many were barred. They now gather on street corners and move in small groups, where heckling and bullying of other teens occur. This displacement from a semi-supervised commercial space to unsupervised public space is the specific mechanism Approach B targets.
- **Sentinel event:** the Old West End Festival shooting [CONFIRM details]. A dispute between two armed young men escalated to gunfire in a crowd. Dispute-to-weapon escalation is the behavior Approach A trains against and the risk Approach B's credible messengers interrupt.

### 3.2 Theory of change
- **Shared risk and protective factors** (CDC Technical Package for Preventing Youth Violence, 2016) include connectedness to caring adults, skill-based self-regulation, safe out-of-school environments, and economic and food security.
- **Developmental fit.** Erikson's *industry vs. inferiority* (≈8–11) and *identity vs. role confusion* (≈12–18), plus *intimacy vs. isolation* for 18–24, describe what a young person's behavior is "about". Piaget's concrete-to-formal operational transition describes which instruction can land. ICT's curriculum already encodes this mapping (ict.edmhs.us/approach). The YVPC tests it formally as a moderator (H1c).
- **Mechanism of martial arts.** Controlled contact with rules, a referee and a stopping point gives repeated practice at *choosing to stop*. Visible, earned rank counters a deficit-based identity, and a stable cohort with the same instructors supplies the relationship that does the work. Prior trials of traditional (philosophy-integrated) martial arts report reductions in aggression and gains in self-regulation (Zivin et al., 2001; Lakes & Hoyt, 2004). A meta-analysis reports small-to-moderate reductions in externalizing behavior (Harwood, Lavidor & Rassovsky, 2017) [CONFIRM citations]. The evidence base is thin on rigorous, community-delivered trials with youth ≥15. That gap is a contribution this Center makes.
- **Mechanism of place.** Place-based and routine-activity approaches show that changing *where and how* youth spend unsupervised time changes violence. Examples include vacant-lot greening (Branas et al., 2018), summer youth employment (Heller, 2014), and CBT-informed programming for at-risk youth (Heller et al., 2017, *Becoming a Man*). Food insecurity is independently associated with adolescent aggression and misconduct [CONFIRM: Jackson & Vaughn 2017 and related].

### 3.3 Innovation
1. Developmental-stage-keyed violence prevention, with stage recorded as data and tested as a moderator.
2. A youth employment ladder inside the intervention: 18–24 peer mentors are themselves the highest-risk age band.
3. A community-level intervention designed around an observed displacement mechanism (restaurant exclusion → corner congregation).
4. Privacy-by-design infrastructure (KATA): role-based access, consent versioning, Ohio mandated-reporting workflows, and analytics only on a de-identified schema.
5. Wearable-sensor and geocoded-event feasibility sub-study (Year 3+, optional and IRB-gated). It tests whether heart-rate and electrodermal signals plus geocoded incident data can inform *community-level* hot-spot timing. **No individual-level surveillance or police data sharing.**

---

## 4. Approach

### 4.1 Core Element 1: Administrative capacity
- **Center structure:** Director (PI) · Evaluation Director (university co-I) · Program Manager · Data Manager (KATA) · Community Engagement Lead · Training Director.
- **Infrastructure:** KATA/ICT PostgreSQL platform (intake, consent, cohorts, attendance, fidelity, referrals, mandated reports, de-identified analytic views), with collaborative access between kata.edmhs.us (clinical and safety) and ict.edmhs.us (program). Six roles: administrator, clinician, facilitator, program manager, analyst, intake coordinator. Analysts see only de-identified views.
- **Compliance:** 2 CFR 200 (45 CFR 75) financial management and Single Audit readiness; Ohio ORC 2151.421 (mandated reporting), ORC 5122.04 (minor behavioral-health consent), ORC 3707.511; HIPAA where NHA clinical data are linked under a BAA and DUA; 42 CFR Part 2 controls if SUD records are ever touched.
- **Translation and dissemination:** quarterly briefs, an annual community report, peer-reviewed papers, and the edmhs.org literature hub.

### 4.2 Core Element 2: Research and rigorous evaluation

#### Approach A: Inner Combat Training (individual and relationship level)
| Component | Detail |
|---|---|
| Dose | 2 sessions/week × 2.5 h, 24 weeks per cycle (5-week cycle 1, then 6-week blocks with a rest week, per the existing curriculum); Qi Gong breathing opens every session |
| Content | Stances, forms and controlled sparring paired weekly with one SEL skill (respect; breathe-then-choose; frustration tolerance; self-control; confidence); conflict de-escalation and disengagement drills |
| Developmental bands | 10–11 (industry; concrete operational) · 12–14 (identity onset; concrete→formal) · 15–17 (identity; formal operational: trigger mapping, values clarification, teaching younger students) · 18–24 (intimacy and generativity: paid peer mentors and assistant instructors with a credential pathway) |
| Clinical boundary | Facilitators teach and do not treat. Licensed referral via NHA behavioral health, with documented, auditable hand-off |
| Design | Individually randomized waitlist-controlled trial, 1:1, stratified by developmental band and sex; 3 annual recruitment waves |
| Sample | N=360 (180/arm). Power: 80% power at α=.05 to detect d=0.30 on the fighting frequency scale, allowing 20% attrition [verify with ICC and baseline variance once pilot data exist] |
| Outcomes | Primary: physical fighting (past 30 days, YRBS items). Secondary: bullying perpetration and victimization (Illinois Bully Scale), weapon carrying, school suspensions (TPS records with consent), self-regulation (DERS-SF), adult connectedness, assault-related ED visits (NHA/EHR linkage with consent) |
| Analysis | Intention-to-treat; generalized linear mixed models (negative binomial for counts) with random intercepts for cohort; mediation (self-regulation, connectedness) via causal mediation; moderation by developmental band; CACE for dose |
| Fidelity | Session checklists in KATA; 10% observed sessions; attendance-based dose |

#### Approach B: Corner-to-Commons (community level)
| Component | Detail |
|---|---|
| What | 8 micro-sites (church halls, rec centers, a partnering restaurant's community room, school gyms) open 3:00–8:00 p.m. on school days and Friday and Saturday evenings. Each provides a hot meal or substantial snack (USDA CACFP At-Risk Afterschool Meals reimbursement), youth-run activity programming, homework space, and two credible-messenger outreach workers who walk the adjacent corners and invite youth in |
| Business partnership | Agreements with the local fast-food restaurant and corner stores: staff refer barred or disruptive youth to the commons instead of calling police for non-criminal behavior; the restaurant community room may host a site [CONFIRM partner] |
| Youth leadership | Youth Advisory Council members (paid) co-design activities and set site rules |
| Design | Stepped-wedge cluster rollout (2 sites activate per quarter over Year 2), with comparative interrupted time series and synthetic control (donor pool: comparable Toledo block groups outside the corridor) |
| Outcomes | Primary: TPD calls for service coded youth disturbance, fight or assault within 400 m of a site during operating hours. Secondary: assault-injury ED visits (ages 10–24, home ZIP); school-day incidents; perceived neighborhood safety (youth and resident surveys); displacement test (100–400 m buffer rings) |
| Analysis | Segmented regression with ARIMA errors; generalized synthetic control; spatial displacement and diffusion-of-benefit indices; cost per incident averted |

**Cross-approach analyses.** Participants of both approaches are tracked (with consent) to test additive effects. Food insecurity (USDA 6-item) and Medicaid status serve as stratifiers for Aim 3.

**Human subjects.** Minors require 45 CFR 46 Subpart D protections, guardian permission and youth assent; young adults consent directly. A Certificate of Confidentiality applies. The IRB of record is the university partner. A DSMB-style safety monitoring plan covers sparring injuries and disclosures.

**Data management and sharing.** A Data Management and Sharing Plan provides a de-identified analytic dataset via ICPSR/NACJD after the primary publications. Variable-level dictionaries are generated from the KATA schema.

### 4.3 Core Element 3: Collaboration and engagement
- **Youth Advisory Councils:** one per intervention community (Junction/Englewood; Old West End; 43620 corridor), 8–12 youth aged 14–24, paid stipends, meeting monthly, with authority over site rules, recruitment messaging and dissemination products.
- **Community Partner Board** (quarterly), with letters of support [CONFIRM each]:

| Partner | Role |
|---|---|
| Neighborhood Health Association (NHA) | School-based clinics; behavioral-health referral; ED/EHR linkage with consent |
| Soul City Wrestling and Boxing Clubs | Training floor; coaches; neighborhood standing |
| Toledo Public Schools | Recruitment; attendance and discipline data under FERPA agreement |
| [University: UToledo / BGSU] | Evaluation, IRB, early-career training |
| City of Toledo violence-prevention office [CONFIRM program name] | Coordination with outreach and violence interruption |
| Toledo Police Department | De-identified calls-for-service data only |
| Local restaurants and corner stores | Referral agreements; site hosting |
| Lucas County Juvenile Court; faith institutions; Toledo-Lucas County Public Library | Referral, sites, dissemination |

### 4.4 Core Element 4: Training and education
- **Early-career researchers (ECRs):** 2–3 per year (postdocs, junior faculty, MPH/PhD students). Each leads one secondary analysis, co-authors at least one paper, and completes a community-engaged research practicum on a Youth Advisory Council.
- **Curriculum:** violence epidemiology; causal inference for community trials (ITS, synthetic control, stepped-wedge); developmental science (Erikson and Piaget in program design); data ethics with minors; R and Python reproducible workflows on the de-identified KATA views.
- **Community workforce:** peer mentors (18–24) earn facilitator credentials; outreach workers receive de-escalation and trauma-informed care training.
- Hosted under **edmhs.org → Training & Education**, alongside the PMSG (Pain Management Support Group) educational program.

---

## 5. Evaluation plan and performance measures ⚠
| Domain | Measure | Source | Frequency |
|---|---|---|---|
| Reach | Enrolled youth by band, ZIP, sex, Medicaid status | KATA intake | Monthly |
| Dose and fidelity | Attendance, fidelity checklist score | KATA | Weekly |
| Individual outcomes | Fighting, bullying, weapons, DERS-SF, connectedness | Surveys (REDCap or KATA forms) | 0, 6, 12 months |
| Community outcomes | Calls for service, ED assault visits | TPD, NHA/hospital | Monthly |
| Engagement | YAC meetings held, recommendations adopted | Minutes | Quarterly |
| Training | ECRs trained, products | Center records | Annual |
| Safety | Injuries, disclosures, mandated reports, referrals completed | KATA | Continuous |

---

## 6. Organizational capacity and key personnel ⚠
- **Darrell A. Hall, MD, MSCIS (PI/Director):** residency-trained family physician (Medical College of Ohio), 14 years in community and inner-city practice; MS in Computer Information Systems (Boston University); certified Professional Data Scientist (2022); former USAF communications-electronics officer (EUCOM, Defense Data Network); 50 years of martial arts training (Goju Ryu, Shaolin, Qi Gong, Yang-style Tai Chi). Designer of ICT, KATA, PMSG and NABS.
- **Evaluation Director:** [university co-investigator, violence epidemiology or prevention science, with a track record of R01-level research] **(critical hire or commitment by Jan 5, 2027).**
- **Program Manager; Data Manager; Community Engagement Lead (credible messenger); Training Director.**
- Biosketches in NIH format; Letters of Support; Facilities and Other Resources (Soul City gym; NHA clinics; KATA cloud infrastructure).

---

## 7. Budget summary, Year 1 (≤ $1,200,000 total costs) ⚠
| Category | Amount | Notes |
|---|---:|---|
| Personnel (PI 0.5 FTE, PM 1.0, Data Mgr 1.0, Engagement Lead 1.0, 4 instructors 0.5, 4 outreach workers 1.0) | $468,000 | Include fringe separately per institution |
| Fringe (≈28%) | $131,000 | |
| Youth stipends (peer mentors 18–24; YAC members) | $96,000 | Participant incentives and youth employment |
| Participant incentives (surveys) | $18,000 | $25–$40 per wave |
| Food (net of CACFP reimbursement) | $60,000 | Approach B commons meals |
| Supplies and equipment (gear, mats, tablets) | $42,000 | Equipment ≥$5,000/unit itemized |
| Travel (CDC grantee meeting, conferences) | $12,000 | |
| Subaward: university evaluation partner | $190,000 | Includes ECR support; first $50K of each subaward in MTDC (2 CFR 200.1, updated threshold) |
| Subaward: EDM Health Services, LLC (KATA platform, hosting, security) | $60,000 | No fee or profit |
| Other: site rental, insurance, IRB, data agreements | $30,000 | |
| **Direct total** | **$1,107,000** | |
| Indirect (de minimis 15% of MTDC, or negotiated rate) | ≈$93,000 | Adjust after the MTDC base calculation |
| **Total** | **≈$1,200,000** | |

---

## 8. Timeline (5 years)
| Year | Approach A (ICT) | Approach B (Commons) | Engagement and training |
|---|---|---|---|
| Y1 (Sep 2027–Sep 2028) | IRB, measures, staff training, wave-1 recruitment (n=120) | Site agreements, baseline ITS data (≥24 months historical) | YACs seated; ECR cohort 1 |
| Y2 | Wave 2 (n=120); 6/12-month follow-ups | Stepped-wedge activation of 8 sites | Community report 1 |
| Y3 | Wave 3 (n=120); interim analysis | Full operation; displacement analysis | Wearable feasibility sub-study (optional) |
| Y4 | Final follow-ups | Sustainment, cost analysis | Manuscripts |
| Y5 | Primary outcome papers | Toolkit and replication guide | Data deposit; dissemination |

---

## 9. Sustainability
Medicaid-reimbursable components (NHA behavioral-health referral and care coordination); CACFP meal reimbursement; Ohio Attorney General / OCJS violence-prevention funds; city ARPA-successor and general-fund violence-prevention lines; philanthropic partners (Toledo Community Foundation [CONFIRM]); revenue-neutral restaurant and business partnerships. The GPCS grant-writing system (§10) is the pipeline for identifying and drafting these follow-on proposals.

## 10. Attachments checklist (SF424 R&R research package) [NOFO]
SF424 (R&R) · Project/Performance Site Locations · R&R Other Project Information (Summary/Abstract, Project Narrative, Bibliography, Facilities & Other Resources, Equipment) · R&R Senior/Key Person Profiles (biosketches) · R&R Budget plus subaward budgets · PHS 398 Research Plan (Specific Aims, Research Strategy) · PHS Human Subjects and Clinical Trials Information (Subpart D) · Letters of Support · Data Management and Sharing Plan · Indirect cost rate agreement or de minimis statement · Disclosure of Lobbying Activities (SF-LLL) · Key Personnel CVs · Organizational chart · Logic model.

## References (verify each before submission)
- David-Ferdon C, Vivolo-Kantor AM, Dahlberg LL, et al. *A Comprehensive Technical Package for the Prevention of Youth Violence and Associated Risk Behaviors.* CDC; 2016.
- Heller SB. Summer jobs reduce violence among disadvantaged youth. *Science.* 2014;346(6214):1219–1223.
- Heller SB, Shah AK, Guryan J, et al. Thinking, fast and slow? Some field experiments to reduce crime and dropout in Chicago. *Q J Econ.* 2017;132(1):1–54.
- Branas CC, South E, Kondo MC, et al. Citywide cluster randomized trial to restore blighted vacant land and its effects on violence, crime, and fear. *PNAS.* 2018;115(12):2946–2951.
- Zivin G, Hassan NR, DePaula GF, et al. An effective approach to violence prevention: traditional martial arts in middle school. *Adolescence.* 2001;36(143):443–459.
- Lakes KD, Hoyt WT. Promoting self-regulation through school-based martial arts training. *J Appl Dev Psychol.* 2004;25(3):283–302.
- Harwood A, Lavidor M, Rassovsky Y. Reducing aggression with martial arts: a meta-analysis of child and youth studies. *Aggress Violent Behav.* 2017;34:96–101.
- Hawkins JD, Oesterle S, Brown EC, et al. Results of a type 2 translational research trial to prevent adolescent drug use and delinquency (Communities That Care). *Arch Pediatr Adolesc Med.* 2009;163(9):789–798.
- Erikson EH. *Identity: Youth and Crisis.* Norton; 1968. · Piaget J, Inhelder B. *The Psychology of the Child.* Basic Books; 1969.
