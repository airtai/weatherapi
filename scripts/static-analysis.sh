#!/usr/bin/env bash
set -e

echo "Running mypy..."
# mkdir -p .
mypy

echo "Running bandit..."
bandit -c pyproject.toml -r weatherman

echo "Running semgrep..."
semgrep scan --config auto --error
