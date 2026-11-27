# Application package templates (mirror of packages.py)
.comp <- function(id, title, kind, required = TRUE, kb_keys = character(), answers = character(),
                  applies_to = c("nonprofit", "for_profit"), page_limit = NA_real_) {
  list(id = id, title = title, kind = kind, required = required, kb_keys = kb_keys, answers = answers,
       applies_to = applies_to, page_limit = page_limit)
}

gpcs_packages <- function() {
  list(
    sf424_rr = list(id = "sf424_rr", name = "SF424 (R&R) research package (NIH/CDC eRA)", components = list(
      .comp("sf424_rr", "SF424 (R&R) cover", "form", kb_keys = c("org.legal_name", "org.uei", "org.ein", "org.address")),
      .comp("sites", "Project/Performance Site Locations", "form", kb_keys = c("org.address", "program.population.zip_codes")),
      .comp("abstract", "Project Summary/Abstract", "narrative", kb_keys = "program.summary",
            answers = c("purpose", "population", "approach"), page_limit = 1),
      .comp("aims", "Specific Aims", "narrative", answers = c("evaluation", "approaches", "priority research"), page_limit = 1),
      .comp("strategy", "Research Strategy", "narrative",
            kb_keys = c("program.summary", "program.developmental_bands", "evidence"),
            answers = c("rigorous evaluation", "priority research", "approaches", "Research and Rigorous Evaluation",
                        "communities with rates", "higher than the national average"), page_limit = 12),
      .comp("admin", "Administrative Capacity / Center structure", "narrative",
            kb_keys = c("org.leadership", "org.financials", "kata.summary"),
            answers = c("Administrative Capacity", "administrative infrastructure", "translation and dissemination")),
      .comp("engagement", "Collaboration & Engagement plan (incl. Youth Advisory Council)", "narrative",
            kb_keys = "org.partners", answers = c("Collaboration and Engagement", "partnerships", "youth advisory council")),
      .comp("training", "Training & Education plan (early career researchers)", "narrative",
            answers = c("Training and Education", "early career researchers")),
      .comp("bibliography", "Bibliography & References Cited", "attachment", kb_keys = "evidence"),
      .comp("facilities", "Facilities & Other Resources", "attachment", kb_keys = c("kata.summary", "org.partners")),
      .comp("keypersons", "R&R Senior/Key Person Profiles + Biosketches", "form", kb_keys = "org.leadership"),
      .comp("budget", "R&R Budget + Budget Justification", "form", kb_keys = "org.financials"),
      .comp("human_subjects", "PHS Human Subjects & Clinical Trials Information", "form",
            kb_keys = "program.safeguards", answers = "youth aged"),
      .comp("dmsp", "Data Management and Sharing Plan", "attachment", kb_keys = "kata.data_use"),
      .comp("letters", "Letters of Support", "attachment", kb_keys = "org.partners", answers = "partnerships"),
      .comp("irs_letter", "IRS 501(c)(3) determination letter (if claimed)", "attachment", FALSE,
            kb_keys = "org.tax_status", applies_to = "nonprofit"),
      .comp("audit", "Most recent audit / Single Audit status", "attachment", FALSE,
            kb_keys = "org.financials.audit", applies_to = "nonprofit"),
      .comp("no_fee", "Statement: no profit or fee charged (2 CFR 200.400(g))", "attachment",
            kb_keys = "org.financials", applies_to = "for_profit"),
      .comp("fin_statements", "Financial statements (2 yrs)", "attachment",
            kb_keys = "org.financials.statements", applies_to = "for_profit"))),
    sf424 = list(id = "sf424", name = "SF-424 standard (non-research) package", components = list(
      .comp("sf424", "SF-424 Application for Federal Assistance", "form", kb_keys = c("org.legal_name", "org.uei", "org.ein")),
      .comp("abstract", "Project Abstract Summary", "narrative", kb_keys = "program.summary"),
      .comp("need", "Statement of Need", "narrative", answers = c("need", "population", "higher than")),
      .comp("approach", "Project Approach / Work Plan", "narrative", kb_keys = "program.summary", answers = c("approach", "should")),
      .comp("evaluation", "Evaluation & Performance Measurement", "narrative", answers = c("evaluation", "performance")),
      .comp("capacity", "Organizational Capacity", "narrative", kb_keys = c("org.leadership", "org.partners")),
      .comp("letters", "Letters of Commitment", "attachment", kb_keys = "org.partners"),
      .comp("irs_letter", "IRS determination letter", "attachment", FALSE, applies_to = "nonprofit"),
      .comp("no_fee", "No profit/fee statement", "attachment", applies_to = "for_profit")))
  )
}

select_package <- function(sol) gpcs_packages()[[if (isTRUE(sol$is_research)) "sf424_rr" else "sf424"]]
