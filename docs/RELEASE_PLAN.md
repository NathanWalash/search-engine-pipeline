# Release and Tag Plan

Use this plan to provide explicit evidence for the brief's Git expectations
(`tags/releases` plus clear milestone progression).

## Current State

- local branch: `feature/final-polish`
- tags strategy: milestone tags on stable merge commits plus one submission-candidate tag
- tags created and pushed:
  - `v0.1-core-roadmap-complete`
  - `v0.2-advanced-search-complete`
  - `v0.3-benchmarking-complete`
  - `v1.0-submission-candidate`
- next step: attach GitHub release notes to each tag

## Proposed Milestone Tags

Use annotated tags tied to meaningful merged states on `main`:

1. `v0.1-core-roadmap-complete`
2. `v0.2-advanced-search-complete`
3. `v0.3-benchmarking-complete`
4. `v1.0-submission-candidate`
5. `v1.0-submission-freeze`

Selected mapping:

- `v0.1-core-roadmap-complete` -> merge commit `9b8685b`
- `v0.2-advanced-search-complete` -> merge commit `5651aa1`
- `v0.3-benchmarking-complete` -> merge commit `fec91a4`
- `v1.0-submission-candidate` -> branch commit `feature/final-polish` head
- `v1.0-submission-freeze` -> final reviewed `main` commit immediately before submission

Note: `v1.0-submission-candidate` provides interim evidence while final review
is in progress. Create `v1.0-submission-freeze` only at the exact commit used
for final submission packaging.

## Tag Commands (When Ready)

```bash
git checkout main
git pull --ff-only origin main
git tag -a v0.1-core-roadmap-complete 9b8685b -m "Core roadmap complete"
git tag -a v0.2-advanced-search-complete 5651aa1 -m "Advanced search features complete"
git tag -a v0.3-benchmarking-complete fec91a4 -m "Benchmarking feature set complete"
git checkout feature/final-polish
git tag -a v1.0-submission-candidate <sha> -m "Submission candidate snapshot"
# later, once final branch is merged and approved:
# git checkout main
# git pull --ff-only origin main
# git tag -a v1.0-submission-freeze <sha> -m "Submission freeze snapshot"
git push origin --tags
```

## Release Notes Template

For each GitHub release:

- scope: which features are included
- quality: test count and coverage percentage
- CI: workflow status summary
- performance: benchmark run count and key timing highlights
- artifacts: whether `data/index.json` is included for submission packaging

## Evidence Checklist

- tag list visible in GitHub repository
- release pages visible with notes for each milestone
- one screenshot or URL list prepared for video/report support
