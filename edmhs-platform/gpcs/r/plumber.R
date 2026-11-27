# GPCS R API (consumed by the Angular UI). Run: Rscript -e 'plumber::pr_run(plumber::pr("plumber.R"), port=8001)'
for (f in list.files("R", full.names = TRUE)) source(f)
KB_ROOT <- Sys.getenv("GPCS_KB", "../../knowledge_base")

#* @filter cors
function(req, res) {
  res$setHeader("Access-Control-Allow-Origin", Sys.getenv("CORS_ORIGINS", "http://localhost:4200"))
  res$setHeader("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
  res$setHeader("Access-Control-Allow-Headers", "Content-Type")
  if (req$REQUEST_METHOD == "OPTIONS") { res$status <- 200; return(list()) }
  plumber::forward()
}

#* @get /health
function() list(ok = TRUE, engine = "R", kb = normalizePath(KB_ROOT))

#* @get /intake/<applicant_type>
function(applicant_type) intake_questions(applicant_type)

#* Analyze a solicitation given as plain text (JSON body: {"text": "..."})
#* @post /analyze
function(req) unclass(parse_solicitation_text(jsonlite::fromJSON(req$postBody)$text))

#* Crosswalk for an org/program against solicitation text
#* @post /crosswalk
function(req, org, program) {
  sol <- parse_solicitation_text(jsonlite::fromJSON(req$postBody)$text)
  cw <- build_crosswalk(sol, load_kb(KB_ROOT, org, program))
  list(crosswalk = unclass(cw), markdown = crosswalk_markdown(cw))
}
