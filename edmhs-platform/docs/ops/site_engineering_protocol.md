# Site Engineering Protocol (SEP-1)

*EDMHS.org and EDM Health Services sites · v1.0 · adopted 2026-11-27 · owner: Darrell A. Hall, MD (Site Engineering Lead)*

**Purpose:** know every day which sites work and which don't. Every failure becomes a tracked engineering task, and once a week the results are reviewed alongside all engineering work opened and closed that week.

---

## 1. Scope: the site inventory

The authoritative list is `ops/sites.yaml`. To add or retire a site, edit that file; the protocol covers whatever it lists.

| Site | URL | Critical | Status | Task repo |
|---|---|---|---|---|
| EDMHS.org (nonprofit hub) | https://edmhs.org | | planned (domain owned at Network Solutions; goes live at the Firebase cutover) | edmhs-org (staging: tweets repo) |
| EDMHS company home | https://www.edmhs.us | | live | edmhs-dash |
| Portfolio & consulting | https://consulting.edmhs.us | | live | edmhs-consulting |
| **Inner Combat Training** | https://ict.edmhs.us | **yes** | live | ict-site |
| **KATA** (staff sign-in) | https://kata.edmhs.us | **yes** | live | edm-platform |
| PMSG | https://pmsg.edmhs.us | | live | pmsg-platform |
| PMSG curriculum hub | https://curriculum-pmsg.edmhs.us | | live | pmsg-platform |
| NABS | https://nabs.edmhs.us | | live | nabs |
| VOX LAB (staff sign-in) | https://voxlab.edmhs.us | | live | edm-platform |
| EDMHS app | https://app.edmhs.us | | live | edm-platform |

**Critical** means families or staff depend on it (enrollment, records, safety workflows).

Domains (registration expiry is checked weekly): **edmhs.org** (Network Solutions), **edmhs.us**.

---

## 2. Definitions

### Verdicts (per site, per day)
| Verdict | Meaning |
|---|---|
| 🟢 **UP** | Expected HTTP status, content marker present, no broken same-site links, certificate valid for at least 21 days, response under 3 s. |
| 🟡 **DEGRADED** | Reachable but impaired: slow (over 3 s), wrong or blank content, broken internal links or pages, health endpoint failing, certificate expiring within 21 days, or an unexpected 4xx. |
| 🔴 **DOWN** | No response (DNS, TLS, timeout or refused), HTTP 5xx or 404 on the home page, or a certificate expiring within 3 days. |
| ⚪ **PLANNED** | Listed but not launched. Reported, never counted as a failure. |

### Severity
| Severity | Rule | Response target | Resolution target |
|---|---|---|---|
| **SEV1** | A **critical** site is DOWN | Acknowledge the same day; status note on the site or by phone to partners if over 4 h | Restore within 24 h |
| **SEV2** | A non-critical site is DOWN, **or** a critical site is DEGRADED | Acknowledge within 1 business day | Fix within 3 business days |
| **SEV3** | A non-critical site is DEGRADED | Triage at the weekly review | Schedule within 2 weeks |
| Info | Hygiene findings, such as a missing HSTS header | Weekly review | Backlog |

### Engineering task
Any GitHub **issue or pull request** in a repository listed under `task_repos` in `ops/sites.yaml`. Incidents found by the daily review are opened automatically as issues labeled `site-incident` plus `sev1`, `sev2` or `sev3`, so they flow into the same open and closed counts.

---

## 3. Daily review: per site, every day

Runs automatically at **10:43 UTC (5:43 a.m. Eastern)** from GitHub Actions (`.github/workflows/site-review.yml`), from GitHub's network, not from any one person's computer.

| Step | What happens | Tool |
|---|---|---|
| D1 | For every site: DNS, HTTP status, response time, content marker, TLS days left, HSTS, extra pages, up to 25 same-site links on the home page, and the health endpoint where one exists | `ops/sitecheck.py` |
| D2 | Write `ops/reports/daily/YYYY-MM-DD.json` (machine) and `.md` (human), and post the table to the run summary | same |
| D3 | **Incidents to tasks.** Each DOWN or DEGRADED site gets **one** open issue `[site] <id> is not healthy` (labels: `site-incident`, severity). While the problem persists, each day adds a comment. When the site is UP again, the issue is closed with a recovery note. | `ops/incidents.py` |
| D4 | Commit the reports. These commits never trigger a deploy. | workflow |
| D5 | **SEV1:** the run fails (red X), which sends GitHub's failure notification email to the repository owner | workflow |

**Human step (2 minutes):** read the daily email or the run summary. For any SEV1 or SEV2, comment on the incident issue with the suspected cause and next action (acknowledgment). Anything else waits for the weekly review.

Run it by hand at any time with `python ops/sitecheck.py`, or with **Run workflow** in GitHub Actions.

---

## 4. Weekly review: aggregate, every Monday

Builds automatically at **11:07 UTC Monday**, covering the previous Monday through Sunday.

| Step | What happens | Tool |
|---|---|---|
| W1 | Aggregate the 7 daily reports: availability % per site, the day-by-day trend, median response time, certificate days left, and every problem logged | `ops/weekly.py` |
| W2 | Domain registration expiry for edmhs.org and edmhs.us (⚠ under 60 days) | same (RDAP) |
| W3 | **Engineering tasks across all task repos:** issues and PRs *opened this week*, *closed this week*, and *open now* | same (GitHub search API) |
| W4 | Write `ops/reports/weekly/YYYY-Www.md` and open it as an issue labeled `weekly-review` | workflow |

**Human review (30 minutes, Monday):** work through the weekly-review issue using this agenda, then close the issue as the sign-off record.
1. **Availability:** any live site under 99% (about 1.7 h down in a week)? Any critical site with any DOWN day?
2. **Incidents:** for each `site-incident` opened this week, was it resolved within the severity target? If not, what blocks it?
3. **Open tasks:** re-prioritize anything open more than 14 days; close what is no longer relevant (with a reason).
4. **Closed tasks:** confirm fixes held (the trend line stays green after the close date).
5. **Expiries:** certificates under 21 days, domains under 60 days.
6. **Decisions:** record changes to the inventory (`ops/sites.yaml`), owners or targets in the issue.

**Metrics tracked week over week:** availability per site; incidents by severity; mean time to restore (open to close of `site-incident`); engineering tasks opened vs. closed (net backlog change).

---

## 5. Runbooks: first response by symptom

| Symptom in report | Likely cause | First action |
|---|---|---|
| `no response: URLError ... Name or service not known` | DNS record missing or changed; domain expired | Check the registrar (Network Solutions for edmhs.org) and DNS records; check the domain expiry in the weekly report |
| `no response: SSL...` / certificate days ≤ 3 | Certificate not renewed (Firebase renews automatically once DNS verifies) | Firebase console → Hosting → domain status; confirm the DNS records still match what Firebase shows |
| HTTP 404 on the home page | Wrong deploy or empty `public` folder | Redeploy the last good version (Firebase Hosting → Release history → Rollback) |
| HTTP 5xx / health endpoint failing | Cloud Run or database problem | Cloud Run logs for `edmhs-api`; Cloud SQL instance status; roll back to the previous Cloud Run revision |
| Content marker missing | Blank page, placeholder, or another site deployed to this domain | Check the hosting target mapping (`.firebaserc` targets) |
| Broken same-site links | Renamed or deleted page | Fix the link, or add a redirect in `firebase.json` |
| Slow (over 3 s) | Cold start or heavy assets | Cloud Run `--min-instances 1` for critical APIs; compress images |

---

## 6. Change control
- Deploys go through the `deploy` workflow on `main` only (tested first). No manual uploads to production except a documented rollback.
- A deploy that changes a critical site needs a pull request. The next daily review is the post-deploy check; for critical sites also run `python ops/sitecheck.py` right after deploying.
- **DNS changes at Network Solutions** (for example the edmhs.org cutover to Firebase): change only the website records (A/AAAA for `edmhs.org`, CNAME or A for `www`) plus the Firebase verification TXT record. **Never remove MX or email-related TXT (SPF/DKIM) records**, or email stops. Screenshot the existing DNS records before any change.

---

## 7. Setup checklist
- [ ] Create the `edmhs-org` repository; copy `deploy/github-workflows/site-review.yml` to `.github/workflows/`.
- [ ] Add secret `OPS_READ_TOKEN`: a fine-grained personal access token with **read-only** Issues and Pull requests on every repository in `task_repos`. Without it the weekly task section reads "not collected" rather than showing zero.
- [ ] GitHub → Settings → Notifications → Actions: email on failed workflows (this is the SEV1 alert).
- [ ] Run **Run workflow** once with *weekly* checked to confirm both reports appear.
- [ ] After the edmhs.org Firebase cutover, set `status: live` for `edmhs-org` in `ops/sites.yaml`.
