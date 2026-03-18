# Submission Checklist

Use this checklist for the final packaging pass before submission.

## 1. Sync and Branch State

- pull latest `main`
- confirm clean working tree (`git status --short` has no changes)
- confirm all feature PRs are merged into `main`

## 2. Quality Gates

Run and confirm all pass:

- `python -m ruff check src tests`
- `python -m mypy src`
- `python -m pytest -q`

Record the final snapshot for report/demo notes:

- passing test count
- total coverage percentage

## 3. Build and Generated Artifact

- run CLI: `python -m src.main`
- execute `build`
- confirm build summary is shown
- confirm index saved to `data/index.json`

Submission rule:

- `data/index.json` is generated during development and git-ignored
- generate a fresh copy at submission time, then include it only if required by the brief

## 4. Benchmark Evidence

- run CLI benchmark command: `benchmark --runs 5`
- capture timing output for:
  - build/reindex
  - load
  - TF-IDF and BM25 query timings
  - phrase/proximity query timings
  - corpus stats and index size

## 5. Demo Walkthrough Readiness

- show `build`
- show `load`
- show `print <word>` (existing + missing)
- show `find` examples:
  - basic AND
  - phrase query
  - ranking mode (`--rank bm25`)
  - proximity bonus (`--proximity-bonus on`)
  - snippets (`--snippets on`)
- show `benchmark --runs N`
- show CI/test evidence in terminal

## 6. Documentation Final Pass

- README command examples match CLI behavior
- roadmap docs reflect final completion status
- architecture and feature descriptions match implemented code
