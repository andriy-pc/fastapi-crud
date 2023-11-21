#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"

source "$script_dir/../.venv/bin/activate"

isort \
  --quiet \
  --settings "$script_dir/../pyproject.toml" \
  "$script_dir/.."

black \
  --quiet \
  "$script_dir/.."

mypy \
  --config-file "$script_dir/../pyproject.toml" \
  --cache-dir "$script_dir/../.mypy_cache" \
  "$script_dir/.."

echo -e "\nRunning tests"
cd "$script_dir/.." && \
  coverage run \
  --source=. \
  -m unittest

echo -e "\nCoverage report"
cd "$script_dir/.." && coverage report

echo -e "\nHTML coverage report"
cd "$script_dir/.." && \
  coverage html