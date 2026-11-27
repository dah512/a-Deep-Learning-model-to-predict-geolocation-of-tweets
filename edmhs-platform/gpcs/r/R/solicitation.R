# Solicitation parser (mirror of gpcs/python/gpcs/solicitation.py)

ELIGIBILITY_GROUPS <- list(
  nonprofit = c("Nonprofits non-higher education with 501(c)(3)",
                "Nonprofits non-higher education without 501(c)(3)",
                "Other Native American tribal organizations"),
  for_profit = c("Small businesses", "For-profit organizations other than small businesses"),
  government = c("State governments", "County governments", "City or township governments",
                 "Special district governments", "Federally recognized Native American tribal governments",
                 "Public and Indian housing authorities"),
  education = c("Public and state institutions of higher education",
                "Private institutions of higher education", "Independent school districts"),
  other = c("Unrestricted", "Other", "Individuals")
)

read_solicitation_text <- function(path) {
  if (grepl("\\.pdf$", path, ignore.case = TRUE)) {
    if (requireNamespace("pdftools", quietly = TRUE)) {
      return(paste(pdftools::pdf_text(path), collapse = "\n"))
    }
    return(paste(system2("pdftotext", c("-layout", shQuote(path), "-"), stdout = TRUE), collapse = "\n"))
  }
  paste(readLines(path, warn = FALSE, encoding = "UTF-8"), collapse = "\n")
}

.clean <- function(x) {
  # Byte-safe in any locale: escapes are ASCII, matching uses fixed/useBytes.
  x <- enc2utf8(x)
  for (ch in c(" ", "●", "○", "•")) x <- gsub(ch, " ", x, fixed = TRUE, useBytes = TRUE)
  x <- gsub("’", "'", x, fixed = TRUE, useBytes = TRUE)
  lines <- strsplit(x, "\n", fixed = TRUE)[[1]]
  lines <- trimws(gsub("[ \t]{2,}", " ", lines, useBytes = TRUE))
  lines <- iconv(lines, "UTF-8", "UTF-8", sub = "")
  lines[nzchar(lines)]
}

.after <- function(label, lines) {
  i <- grep(paste0("^", label, "\\s*:?"), lines, ignore.case = TRUE, perl = TRUE)[1]
  if (is.na(i)) return(NA_character_)
  val <- trimws(sub(paste0("^", label, "\\s*:?\\s*"), "", lines[i], ignore.case = TRUE, perl = TRUE))
  if (!nzchar(val) && i < length(lines)) val <- lines[i + 1]
  val
}

.money <- function(s) {
  if (is.na(s)) return(NA_real_)
  m <- regmatches(s, regexpr("[0-9][0-9,]*", s))
  if (!length(m)) NA_real_ else as.numeric(gsub(",", "", m))
}

.date_after <- function(label, txt) {
  m <- regmatches(txt, regexec(paste0(label, "\\s*:\\s*([A-Z][a-z]+\\.? [0-9]{1,2}, [0-9]{4})"), txt,
                               ignore.case = TRUE, perl = TRUE))[[1]]
  if (length(m) == 2) m[2] else NA_character_
}

parse_solicitation_text <- function(raw) {
  lines <- .clean(raw)
  txt <- paste(lines, collapse = "\n")
  flow <- paste(lines, collapse = " ")
  s <- list()
  ai <- grep("^Agency:", lines)[1]
  s$title <- if (!is.na(ai)) paste(lines[seq_len(ai - 1)], collapse = " ") else NA_character_
  s$agency <- .after("Agency", lines)
  s$assistance_listings <- unique(regmatches(txt, gregexpr("[0-9]{2}\\.[0-9]{3}(?= --)", txt, perl = TRUE))[[1]])
  s$status <- NA_character_
  for (st in c("Forecasted", "Posted", "Closed", "Archived")) {
    if (any(lines == st | startsWith(lines, paste0(st, " ")))) { s$status <- tolower(st); break }
  }
  s$dates <- Filter(Negate(is.na), list(
    post = .date_after("(?:Forecasted )?post(?:ed)? date", txt),
    due = .date_after("(?:Forecasted )?(?:application due|close) date", txt),
    award = .date_after("(?:Forecasted )?award date", txt),
    start = .date_after("(?:Forecasted )?project start date", txt)))
  s$fiscal_year <- suppressWarnings(as.integer(.after("Fiscal Year", lines)))
  s$total_funding <- .money(.after("(?:Expected project funding|Estimated Total Program Funding)", lines))
  s$expected_awards <- .money(.after("(?:Expected awards|Expected Number of Awards)", lines))
  s$award_floor <- .money(.after("Award (?:min\\.?|Floor)", lines))
  s$award_ceiling <- .money(.after("Award (?:max\\.?|Ceiling)", lines))
  s$opportunity_number <- .after("Funding opportunity number", lines)
  cs <- .after("Cost sharing or matching requirement", lines)
  s$cost_sharing <- if (is.na(cs)) NA else startsWith(tolower(cs), "y")
  s$instrument <- .after("Funding instrument type", lines)
  s$eligibility <- lines[lines %in% unlist(ELIGIBILITY_GROUPS)]
  am <- regmatches(flow, regexec("aged?\\s+([0-9]{1,2})\\s*(?:to|-|through)\\s*([0-9]{1,2})", flow, perl = TRUE))[[1]]
  s$population_ages <- if (length(am) == 3) as.integer(am[2:3]) else NULL
  sm <- regmatches(flow, regexec("Summary (.*?) Eligibility ", flow, perl = TRUE))[[1]]
  s$summary <- if (length(sm) == 2) sm[2] else NA_character_
  s$core_elements <- list()
  if (!is.na(s$summary)) {
    ce <- gregexpr("([0-9])\\)\\s*([A-Z][A-Za-z ]+?):\\s*(.*?)(?=\\s[0-9]\\)\\s*[A-Z]|$)", s$summary, perl = TRUE)
    parts <- regmatches(s$summary, ce)[[1]]
    s$core_elements <- lapply(parts, function(p) {
      m <- regmatches(p, regexec("^([0-9])\\)\\s*([A-Z][A-Za-z ]+?):\\s*(.*)$", p, perl = TRUE))[[1]]
      list(number = as.integer(m[2]), name = trimws(m[3]), text = trimws(m[4]))
    })
    sent <- strsplit(s$summary, "(?<=[.;])\\s+(?=[A-Z0-9])", perl = TRUE)[[1]]
    s$requirements <- trimws(sent[grepl("\\b(must|should|shall|required|are expected to)\\b", sent, ignore.case = TRUE)])
  }
  s$contacts <- sort(unique(regmatches(txt, gregexpr("[A-Za-z0-9._+-]+@[A-Za-z0-9-]+\\.[A-Za-z.]+", txt))[[1]]))
  s$is_research <- grepl("^(RFA|PAR|PA)-[A-Z]{2}-[0-9]{2}-[0-9]{3}$", s$opportunity_number %||% "") ||
    grepl("investigator-initiated research|rigorous evaluation", flow, ignore.case = TRUE)
  s$implied_years <- if (all(!is.na(c(s$total_funding, s$expected_awards, s$award_ceiling))) && s$award_ceiling > 0)
    round(s$total_funding / (s$expected_awards * s$award_ceiling), 2) else NA_real_
  s$eligible_groups <- eligible_groups(s$eligibility)
  structure(s, class = "gpcs_solicitation")
}

`%||%` <- function(a, b) if (is.null(a) || (length(a) == 1 && is.na(a))) b else a

eligible_groups <- function(eligibility) {
  sort(unique(names(ELIGIBILITY_GROUPS)[vapply(ELIGIBILITY_GROUPS, function(g) any(eligibility %in% g), logical(1))]))
}

parse_solicitation <- function(path) parse_solicitation_text(read_solicitation_text(path))
