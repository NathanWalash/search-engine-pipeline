# Git Workflow Evidence

This document links roadmap delivery to branch/PR/tag history for marking.

## Core Roadmap Traceability

- phase 01 scaffold:
  - merge commit: `5a6943c`
  - tag: `core-phase-01-scaffold`
- phase 02 CLI shell:
  - PR: #2
  - merge commit: `24b7f27`
  - tag: `core-phase-02-cli-shell`
- phase 03 parser normalisation:
  - PR: #3
  - merge commit: `ec18fae`
  - tag: `core-phase-03-parser-normalisation`
- phase 04 crawler core:
  - PR: #1
  - merge commit: `ad1a1cd`
  - tag: `core-phase-04-crawler-core`
- phase 05 indexer core:
  - PR: #5
  - merge commit: `b3ffee8`
  - tag: `core-phase-05-indexer-core`
- phase 06 build pipeline:
  - PR: #6
  - merge commit: `96166c4`
  - tag: `core-phase-06-build-pipeline`
- phase 07 storage:
  - PR: #7
  - merge commit: `ab6f1bd`
  - tag: `core-phase-07-storage-layer`
- phase 08 search commands:
  - PR: #8
  - merge commit: `f8ae62e`
  - tag: `core-phase-08-search-print-find`
- phase 09 testing integration:
  - PR: #9
  - merge commit: `2f3a63f`
  - tag: `core-phase-09-testing-integration`
- phase 10 README/demo readiness:
  - PR: #10
  - merge commit: `d754319`
  - tag: `core-phase-10-demo-readme-ready`

Core milestone release tag:

- `v0.1-core-roadmap-complete` -> `9b8685b`

## Advanced Roadmap Traceability

- feature A TF-IDF:
  - PR: #14
  - merge commit: `ea910f7`
  - tag: `adv-feature-a-tfidf`
- feature B phrase search:
  - PR: #15
  - merge commit: `091203b`
  - tag: `adv-feature-b-phrase-search`
- feature C query suggestions:
  - PR: #16
  - merge commit: `49a14c3`
  - tag: `adv-feature-c-query-suggestions`
- feature D crawl statistics:
  - PR: #17
  - merge commit: `6e77c73`
  - tag: `adv-feature-d-crawl-statistics`
- feature E tokenisation:
  - PR: #18
  - merge commit: `eb68509`
  - tag: `adv-feature-e-tokenisation`
- feature I postings optimisation:
  - PR: #20
  - merge commit: `cd4fc2f`
  - tag: `adv-feature-i-postings-optimisation`
- feature G BM25:
  - PR: #21
  - merge commit: `fc6d57f`
  - tag: `adv-feature-g-bm25`
- feature H proximity bonus:
  - PR: #22
  - merge commit: `53ced3f`
  - tag: `adv-feature-h-proximity-bonus`
- feature F snippets/highlighting:
  - PR: #23
  - merge commit: `5651aa1`
  - tag: `adv-feature-f-snippets-highlighting`
- feature J benchmarking:
  - PR: #24
  - merge commit: `fec91a4`
  - tag: `adv-feature-j-benchmarking`

Advanced milestone release tags:

- `v0.2-advanced-search-complete` -> `5651aa1`
- `v0.3-benchmarking-complete` -> `fec91a4`

## Finalisation Tags

- submission candidate: `v1.0-submission-candidate` -> `8bf59ef`
- final submission freeze (to create at final lock): `v1.0-submission-freeze`

## Notes for Demo and Report

- show `git log --oneline --graph --decorate` to evidence incremental branch-based work
- show `git tag --list` to evidence milestone and phase tags
- show GitHub Releases page to evidence release notes linked to tags
