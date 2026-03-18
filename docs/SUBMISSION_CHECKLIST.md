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
- store final benchmark snapshot in `docs/BENCHMARK_RESULTS.md`

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
- README includes a references section for ranking/query design decisions

## 7. Git Tags and Release Evidence

- create annotated milestone tags (see `docs/RELEASE_PLAN.md`)
- create phase-level tags (core/advanced) for roadmap traceability
- push tags to GitHub (`git push origin --tags`)
- create GitHub releases from milestone tags with short notes:
  - included features
  - test/coverage snapshot
  - benchmark snapshot
- capture release URLs (or screenshots) for demo/report evidence
- keep branch/PR/tag mapping in `docs/GIT_WORKFLOW_EVIDENCE.md`

## 8. Referencing and Research Evidence

- confirm README/docs cite external algorithm references used (BM25/TF-IDF/query processing)
- confirm video/demo notes reference these sources when discussing design decisions
- confirm any tutorial/library sources used are acknowledged
