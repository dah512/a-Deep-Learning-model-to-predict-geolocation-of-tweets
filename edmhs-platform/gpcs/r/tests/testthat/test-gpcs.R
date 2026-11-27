root <- normalizePath(file.path("..", "..", "..", ".."))
pdf <- file.path(root, "gpcs", "python", "tests", "fixtures", "RFA-CE-27-013_forecast.pdf")
kb_root <- file.path(root, "knowledge_base")
sol <- parse_solicitation(pdf)

test_that("core fields parse identically to the Python engine", {
  expect_equal(sol$opportunity_number, "RFA-CE-27-013")
  expect_equal(sol$award_ceiling, 1200000)
  expect_equal(sol$total_funding, 30000000)
  expect_equal(sol$expected_awards, 5)
  expect_false(sol$cost_sharing)
  expect_equal(sol$instrument, "Cooperative agreement")
  expect_equal(sol$dates$due, "February 1, 2027")
  expect_equal(sol$status, "forecasted")
  expect_equal(sol$population_ages, c(10L, 24L))
  expect_equal(sol$implied_years, 5)
  expect_true(sol$is_research)
  expect_true("ncipc_erpo@cdc.gov" %in% sol$contacts)
})

test_that("four core elements and eligibility groups", {
  expect_equal(vapply(sol$core_elements, `[[`, "", "name"),
               c("Administrative Capacity", "Research and Rigorous Evaluation",
                 "Collaboration and Engagement", "Training and Education"))
  expect_true(all(c("nonprofit", "for_profit") %in% sol$eligible_groups))
})

test_that("nonprofit and for-profit crosswalks differ correctly", {
  np <- build_crosswalk(sol, load_kb(kb_root, "edmhs_org", "ict"))
  fp <- build_crosswalk(sol, load_kb(kb_root, "edm_health_services_llc", "ict"))
  expect_true(np$eligible && fp$eligible)
  expect_true("irs_letter" %in% names(np$component_status))
  expect_true("no_fee" %in% names(fp$component_status))
  expect_false("no_fee" %in% names(np$component_status))
  expect_true(any(grepl("org.uei", np$flags, fixed = TRUE)))
  expect_true(any(grepl("profit/fee", fp$flags, fixed = TRUE)))
  expect_true(any(grepl("Population mismatch", np$flags)))
  expect_true(all(lengths(lapply(np$rows[1:4], `[[`, "components")) > 0))
})
