#!/bin/bash -ex

## NOTE: paths may differ when running in a managed task. To ensure behavior is consistent between
# managed and local tasks always use these variables for the project and project type path
PROJECT_PATH=${BASE_PATH}/project
PROJECT_TYPE_PATH=${BASE_PATH}/projecttype

ruff check $PROJECT_PATH/src/*
semgrep scan --config auto $PROJECT_PATH/src/*