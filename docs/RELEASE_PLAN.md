# Release and Tag Plan

Use this plan to evidence professional Git workflow: meaningful branches,
annotated tags, and linked GitHub releases.

## Current State

Last updated: 2026-03-18

- working branch for this evidence pass: `feature/release-evidence-phase-tags`
- milestone tags already pushed:
  - `v0.1-core-roadmap-complete`
  - `v0.2-advanced-search-complete`
  - `v0.3-benchmarking-complete`
  - `v1.0-submission-candidate`
- phase tags: to be added for fuller roadmap traceability
- final freeze tag: `v1.0-submission-freeze` (create on final reviewed `main` commit)

## Tag Map (Milestones + Phases)

### Milestone tags

- `v0.1-core-roadmap-complete` -> `9b8685b`
- `v0.2-advanced-search-complete` -> `5651aa1`
- `v0.3-benchmarking-complete` -> `fec91a4`
- `v1.0-submission-candidate` -> `8bf59ef`
- `v1.0-submission-freeze` -> final locked `main` commit for submission

### Core roadmap phase tags

- `core-phase-01-scaffold` -> `5a6943c`
- `core-phase-02-cli-shell` -> `24b7f27`
- `core-phase-03-parser-normalisation` -> `ec18fae`
- `core-phase-04-crawler-core` -> `ad1a1cd`
- `core-phase-05-indexer-core` -> `b3ffee8`
- `core-phase-06-build-pipeline` -> `96166c4`
- `core-phase-07-storage-layer` -> `ab6f1bd`
- `core-phase-08-search-print-find` -> `f8ae62e`
- `core-phase-09-testing-integration` -> `2f3a63f`
- `core-phase-10-demo-readme-ready` -> `d754319`

### Advanced roadmap feature tags

- `adv-feature-a-tfidf` -> `ea910f7`
- `adv-feature-b-phrase-search` -> `091203b`
- `adv-feature-c-query-suggestions` -> `49a14c3`
- `adv-feature-d-crawl-statistics` -> `6e77c73`
- `adv-feature-e-tokenisation` -> `eb68509`
- `adv-feature-f-snippets-highlighting` -> `5651aa1`
- `adv-feature-g-bm25` -> `fc6d57f`
- `adv-feature-h-proximity-bonus` -> `53ced3f`
- `adv-feature-i-postings-optimisation` -> `cd4fc2f`
- `adv-feature-j-benchmarking` -> `fec91a4`

## Tag Commands

```bash
git checkout main
git pull --ff-only origin main

git tag -a core-phase-01-scaffold 5a6943c -m "Core phase 01: scaffold"
git tag -a core-phase-02-cli-shell 24b7f27 -m "Core phase 02: CLI shell"
git tag -a core-phase-03-parser-normalisation ec18fae -m "Core phase 03: parser normalisation"
git tag -a core-phase-04-crawler-core ad1a1cd -m "Core phase 04: crawler core"
git tag -a core-phase-05-indexer-core b3ffee8 -m "Core phase 05: indexer core"
git tag -a core-phase-06-build-pipeline 96166c4 -m "Core phase 06: build pipeline"
git tag -a core-phase-07-storage-layer ab6f1bd -m "Core phase 07: storage"
git tag -a core-phase-08-search-print-find f8ae62e -m "Core phase 08: search commands"
git tag -a core-phase-09-testing-integration 2f3a63f -m "Core phase 09: testing integration"
git tag -a core-phase-10-demo-readme-ready d754319 -m "Core phase 10: README and demo readiness"

git tag -a adv-feature-a-tfidf ea910f7 -m "Advanced feature A: TF-IDF ranking"
git tag -a adv-feature-b-phrase-search 091203b -m "Advanced feature B: phrase search"
git tag -a adv-feature-c-query-suggestions 49a14c3 -m "Advanced feature C: query suggestions"
git tag -a adv-feature-d-crawl-statistics 6e77c73 -m "Advanced feature D: crawl statistics"
git tag -a adv-feature-e-tokenisation eb68509 -m "Advanced feature E: smarter tokenisation"
git tag -a adv-feature-f-snippets-highlighting 5651aa1 -m "Advanced feature F: snippets"
git tag -a adv-feature-g-bm25 fc6d57f -m "Advanced feature G: BM25"
git tag -a adv-feature-h-proximity-bonus 53ced3f -m "Advanced feature H: proximity bonus"
git tag -a adv-feature-i-postings-optimisation cd4fc2f -m "Advanced feature I: postings optimisation"
git tag -a adv-feature-j-benchmarking fec91a4 -m "Advanced feature J: benchmarking"

git push origin --tags
```

## GitHub Release Plan

Create release entries in this order:

1. `v0.1-core-roadmap-complete`
2. `v0.2-advanced-search-complete`
3. `v0.3-benchmarking-complete`
4. `v1.0-submission-candidate`
5. optional detailed releases for each `core-phase-*` and `adv-feature-*` tag
6. `v1.0-submission-freeze` (final submission lock)

## Windows `gh` Notes

If `gh` is installed but not on `PATH`, use:

```powershell
$GhExe = "C:\Program Files\GitHub CLI\gh.exe"
& $GhExe auth status
```

Create a release from a tag:

```powershell
& $GhExe release create <tag> --title "<title>" --notes "<notes>"
```

## Release Notes Template

- scope: features included by this tag
- quality: test count and coverage percentage
- CI: lint/type/test status
- performance: benchmark command and key timings
- references: mention algorithm sources where relevant
