library(testthat)
for (f in list.files(file.path("..", "R"), full.names = TRUE)) source(f)
test_dir("testthat")
