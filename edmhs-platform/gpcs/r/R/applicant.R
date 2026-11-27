# Applicant profiles: nonprofit vs for-profit (mirror of applicant.py)
.q <- function(key, prompt, why, required = TRUE) list(key = key, prompt = prompt, why = why, required = required)

.common_q <- list(
  .q("legal_name", "Legal name exactly as registered in SAM.gov", "SF424 item 8a must match SAM"),
  .q("uei", "Unique Entity ID (UEI)", "Required for all federal awards (2 CFR 25)"),
  .q("ein", "Employer Identification Number", "SF424 item 8b"),
  .q("sam_status", "SAM.gov registration status and expiration", "Must be active at submission and award"),
  .q("address", "Applicant address, county, congressional district", "SF424; site locations"),
  .q("mission", "Mission statement", "Organizational capacity narrative"),
  .q("leadership", "Program director / PI and key personnel", "Key person profiles"),
  .q("partners", "Partners and status of each letter of support", "Collaboration narrative; letters"),
  .q("financials.indirect_rate", "Negotiated indirect rate, or de minimis 15% MTDC", "2 CFR 200.414"))

intake_questions <- function(applicant_type = c("nonprofit", "for_profit")) {
  applicant_type <- match.arg(applicant_type)
  extra <- switch(applicant_type,
    nonprofit = list(
      .q("tax_status", "501(c)(3) determination letter, or nonprofit without 501(c)(3)", "Eligibility category"),
      .q("board", "Governing board roster", "Capacity; community governance", FALSE),
      .q("financials.audit", "Most recent audit; Single Audit status", "2 CFR 200.501 ($1,000,000 threshold)"),
      .q("financials.annual_budget", "Annual operating budget", "Financial capacity")),
    for_profit = list(
      .q("business_size", "Small business status for primary NAICS (SBA size standard)", "Eligibility category"),
      .q("naics", "Primary NAICS code", "Size standard lookup"),
      .q("ownership", "Owners >= 25% and any foreign ownership/control", "Responsibility review"),
      .q("financials.statements", "Financial statements, last 2 fiscal years", "Financial capability"),
      .q("cage", "CAGE code", "SAM detail", FALSE)))
  c(.common_q, extra)
}

load_profile <- function(path) {
  data <- yaml::read_yaml(path)
  if (!data$applicant_type %in% c("nonprofit", "for_profit")) stop("applicant_type must be nonprofit or for_profit")
  structure(list(data = data, applicant_type = data$applicant_type), class = "gpcs_profile")
}

.dget <- function(x, dotted) {
  for (p in strsplit(dotted, ".", fixed = TRUE)[[1]]) {
    if (!is.list(x) || is.null(x[[p]])) return(NULL)
    x <- x[[p]]
  }
  x
}

.blank <- function(v) {
  is.null(v) || length(v) == 0 || (is.character(v) && length(v) == 1 &&
    (!nzchar(v) || startsWith(v, "TODO") || grepl("not registered", v, fixed = TRUE)))
}

profile_gaps <- function(profile) {
  Filter(function(q) q$required && .blank(.dget(profile$data, q$key)), intake_questions(profile$applicant_type))
}
