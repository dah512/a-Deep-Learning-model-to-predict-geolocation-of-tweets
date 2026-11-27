# Knowledge base + compliance crosswalk (mirror of knowledge.py / crosswalk.py)
load_kb <- function(root, org, program) {
  programs <- lapply(list.files(file.path(root, "programs"), "\\.yaml$", full.names = TRUE), yaml::read_yaml)
  names(programs) <- vapply(programs, `[[`, "", "id")
  ev <- file.path(root, "evidence.yaml")
  structure(list(profile = load_profile(file.path(root, "organizations", paste0(org, ".yaml"))),
                 programs = programs, evidence = if (file.exists(ev)) yaml::read_yaml(ev) else list(),
                 program_id = program), class = "gpcs_kb")
}

kb_get <- function(kb, key) {
  head <- sub("\\..*$", "", key); rest <- if (grepl(".", key, fixed = TRUE)) sub("^[^.]*\\.", "", key) else ""
  if (head == "org") return(.dget(kb$profile$data, rest))
  if (head == "evidence") return(kb$evidence)
  src <- if (head == "program") kb$programs[[kb$program_id]] else kb$programs[[head]]
  if (is.null(src)) return(NULL)
  if (nzchar(rest)) .dget(src, rest) else src
}

.match_components <- function(text, comps) {
  low <- tolower(text)
  hits <- vapply(comps, function(c) any(vapply(tolower(c$answers), function(a) grepl(a, low, fixed = TRUE), logical(1))), logical(1))
  vapply(comps[hits], `[[`, "", "id")
}

build_crosswalk <- function(sol, kb, package = select_package(sol)) {
  atype <- kb$profile$applicant_type
  comps <- Filter(function(c) atype %in% c$applies_to, package$components)
  status <- lapply(comps, function(c) {
    missing <- c$kb_keys[vapply(c$kb_keys, function(k) .blank(kb_get(kb, k)), logical(1))]
    list(title = c$title, kind = c$kind, required = c$required, kb_keys = c$kb_keys, missing = missing,
         coverage = if (length(c$kb_keys)) round(1 - length(missing) / length(c$kb_keys), 2) else 1)
  })
  names(status) <- vapply(comps, `[[`, "", "id")
  row_status <- function(ids) {
    if (!length(ids)) return("unmapped")
    keyed <- ids[vapply(ids, function(i) length(status[[i]]$kb_keys) > 0, logical(1))]
    if (!length(keyed)) return("needs narrative")
    covs <- vapply(keyed, function(i) status[[i]]$coverage, numeric(1))
    if (min(covs) >= 1) "facts available" else if (max(covs) > 0) "partial" else "gap"
  }
  rows <- lapply(sol$core_elements, function(ce) {
    ids <- .match_components(paste(ce$name, ce$text), comps)
    list(requirement = sprintf("Core element %d - %s: %s", ce$number, ce$name, ce$text),
         source = "core_element", components = ids, status = row_status(ids))
  })
  ce_names <- vapply(sol$core_elements, `[[`, "", "name")
  for (req in sol$requirements %||% character()) {
    if (any(vapply(ce_names, function(n) grepl(n, req, fixed = TRUE), logical(1)))) next
    ids <- .match_components(req, comps)
    rows[[length(rows) + 1]] <- list(requirement = req, source = "requirement", components = ids, status = row_status(ids))
  }
  eligible <- !length(sol$eligibility) || atype %in% sol$eligible_groups
  flags <- character()
  if (!eligible) flags <- c(flags, sprintf("BLOCKER: '%s' applicants are not eligible.", atype))
  if (identical(sol$status, "forecasted")) flags <- c(flags, "Forecast only: re-run on the full NOFO when it posts.")
  if (!is.na(sol$implied_years) && sol$implied_years > 1.2)
    flags <- c(flags, sprintf("Ceiling is probably per budget year (~%d-year project period).", round(sol$implied_years)))
  pa <- kb_get(kb, "program.population.current_ages")
  if (!is.null(sol$population_ages) && !is.null(pa) && (pa[1] > sol$population_ages[1] || pa[2] < sol$population_ages[2]))
    flags <- c(flags, sprintf("Population mismatch: solicitation ages %d-%d; program serves %d-%d.",
                              sol$population_ages[1], sol$population_ages[2], pa[1], pa[2]))
  if (atype == "for_profit") flags <- c(flags, "For-profit applicant: budget must exclude profit/fee (2 CFR 200.400(g)).")
  for (k in c("uei", "sam_status")) if (.blank(kb_get(kb, paste0("org.", k))))
    flags <- c(flags, sprintf("BLOCKER until resolved: org.%s missing - SAM.gov registration takes 2-6 weeks.", k))
  structure(list(solicitation = paste(sol$opportunity_number, "-", sol$title), applicant_type = atype,
                 package = package$name, eligible = eligible, rows = rows, component_status = status,
                 profile_gaps = profile_gaps(kb$profile), flags = flags), class = "gpcs_crosswalk")
}

crosswalk_markdown <- function(cw) {
  out <- c(paste("# Compliance crosswalk:", cw$solicitation), "",
           sprintf("Applicant type: **%s** - Package: **%s** - Eligible: **%s**", cw$applicant_type, cw$package,
                   if (cw$eligible) "yes" else "NO"), "", "## Flags", paste("-", cw$flags), "",
           "| # | Requirement | Source | Components | Status |", "|---|---|---|---|---|")
  for (i in seq_along(cw$rows)) {
    r <- cw$rows[[i]]
    out <- c(out, sprintf("| %d | %s | %s | %s | %s |", i, substr(gsub("\\|", "/", r$requirement), 1, 160),
                          r$source, paste(r$components, collapse = ", "), r$status))
  }
  paste(c(out, ""), collapse = "\n")
}
