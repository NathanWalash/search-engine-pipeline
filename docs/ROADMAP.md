# COMP3011 Coursework 2 — Implementation Roadmap
## Agent-Friendly, Phase-Based Development Plan

This roadmap is designed for a **branch-per-feature workflow** with **small, typical commits**.  
Each phase should be completed on its own feature branch, merged only when tests pass and the code remains consistent with `SPECIFICATION.md`.

The guiding principles are:

- keep commits small and reviewable,
- keep each branch focused on one feature area,
- make the baseline coursework requirements solid before adding advanced features,
- leave enhancements until the end,
- preserve a clean Git history that demonstrates incremental engineering.

---

# 1. Workflow Rules

## 1.1 Branch Strategy

Recommended branch naming:

- `feature/project-scaffold`
- `feature/cli-shell`
- `feature/parser-normalisation`
- `feature/crawler-core`
- `feature/indexer-core`
- `feature/storage-load-save`
- `feature/search-print-find`
- `feature/testing-integration`
- `feature/readme-demo`
- `feature/ranking-tfidf`
- `feature/phrase-search`
- `feature/query-suggestions`

Each branch should target **one coherent deliverable**.

## 1.2 Commit Size Rule

Each commit should ideally be:

- one logical change,
- at most a few hundred lines,
- easy to explain in one sentence,
- test-backed where practical.

A good rule is:

- **small structural commit**
- **implementation commit**
- **tests commit**
- **cleanup/refactor commit**

## 1.3 Merge Rule

Only merge a feature branch when:

- the feature works,
- tests pass,
- command-line behaviour still matches the specification,
- no unrelated files were changed,
- commit history is understandable.

---

# 2. Development Order

The project should be built in this order:

1. Project scaffold
2. CLI shell skeleton
3. Parser and token normalisation
4. Crawler core
5. Indexer core
6. Storage layer
7. Search commands
8. Integration and edge-case hardening
9. README and demo prep
10. Advanced features

This order reduces risk because it builds from the **data pipeline inward**:

**crawl → parse → index → store → search**

---

# 3. Phase 1 — Project Scaffold

## Goal

Create the repository structure, dependency setup, and minimal executable shell.

## Branch

`feature/project-scaffold`

## Deliverables

- `src/` directory
- `tests/` directory
- `data/` directory
- `requirements.txt`
- placeholder module files
- initial `README.md`
- `SPECIFICATION.md`
- `.gitignore`

## Suggested Commits

### Commit 1
**Message:** `chore: initialise repository structure`

Create:

- `src/`
- `tests/`
- `data/`

Add placeholder files:

- `src/main.py`
- `src/crawler.py`
- `src/parser.py`
- `src/indexer.py`
- `src/storage.py`
- `src/search.py`

### Commit 2
**Message:** `chore: add dependencies and gitignore`

Add:

- `requirements.txt`
- `.gitignore`

Recommended dependencies:

- `requests`
- `beautifulsoup4`
- `pytest`
- `pytest-cov`

### Commit 3
**Message:** `docs: add initial README and specification`

Add:

- `README.md`
- `SPECIFICATION.md`

## Exit Criteria

- repo structure exists,
- dependencies install successfully,
- project opens cleanly in editor,
- no runtime code yet beyond placeholders.

---

# 4. Phase 2 — CLI Shell Skeleton

## Goal

Create a working command loop with command parsing, but stub behaviour.

## Branch

`feature/cli-shell`

## Deliverables

- interactive shell in `main.py`
- support for:
  - `build`
  - `load`
  - `print <word>`
  - `find <query>`
  - `help`
  - `exit`
- placeholder outputs only

## Suggested Commits

### Commit 1
**Message:** `feat: add interactive CLI shell loop`

Implement:

- command prompt
- user input loop
- exit handling

### Commit 2
**Message:** `feat: add command parsing for build load print and find`

Parse commands into dispatcher logic.

### Commit 3
**Message:** `test: add CLI parsing tests for valid and invalid commands`

Test:

- valid commands
- unknown command
- missing arguments

### Commit 4
**Message:** `refactor: improve CLI error messages and help output`

Polish shell messages.

## Exit Criteria

- commands are recognised,
- invalid input is handled,
- no real crawling/search yet.

---

# 5. Phase 3 — Parser and Normalisation

## Goal

Create the text extraction and tokenisation layer independently from crawling.

## Branch

`feature/parser-normalisation`

## Deliverables

- HTML-to-text extraction
- lowercase normalisation
- punctuation stripping
- token position tracking

## Suggested Commits

### Commit 1
**Message:** `feat: add HTML text extraction utility`

Implement function(s) to:

- parse HTML with BeautifulSoup,
- extract visible text,
- ignore irrelevant markup where appropriate.

### Commit 2
**Message:** `feat: add token normalisation and tokenisation`

Implement:

- lowercase conversion
- punctuation removal
- whitespace splitting
- empty token filtering

### Commit 3
**Message:** `feat: track token positions during parsing`

Return tokens with positions.

### Commit 4
**Message:** `test: add parser and normalisation unit tests`

Test:

- punctuation handling
- case insensitivity
- empty HTML
- repeated words
- position tracking

### Commit 5
**Message:** `refactor: simplify parser interfaces and add docstrings`

Clean interfaces and documentation.

## Exit Criteria

- parser can process raw HTML into ordered normalised tokens,
- behaviour is deterministic,
- parser tests pass.

---

# 6. Phase 4 — Crawler Core

## Goal

Implement the crawler for the target website with politeness enforcement.

## Branch

`feature/crawler-core`

## Deliverables

- request wrapper
- 6-second politeness delay
- internal link extraction
- BFS crawl traversal
- visited-set deduplication
- resilient error handling

## Suggested Commits

### Commit 1
**Message:** `feat: add HTTP request wrapper for page fetching`

Implement:

- GET requests
- timeout
- basic status checking

### Commit 2
**Message:** `feat: enforce politeness delay between requests`

Centralise request timing logic.

### Commit 3
**Message:** `feat: add internal link extraction and URL filtering`

Only follow links inside `quotes.toscrape.com`.

### Commit 4
**Message:** `feat: implement BFS crawler with visited tracking`

Add:

- crawl queue
- visited set
- iterative traversal

### Commit 5
**Message:** `test: add crawler tests with mocked HTTP responses`

Test:

- success response
- failed response
- duplicate links
- internal link filtering
- politeness timing logic

### Commit 6
**Message:** `refactor: harden crawler error handling and logging`

Improve resilience and clarity.

## Exit Criteria

- crawler can traverse the target site,
- crawler respects politeness rule,
- duplicate URLs are not revisited,
- crawler failures do not crash the full build unexpectedly.

---

# 7. Phase 5 — Indexer Core

## Goal

Build the inverted index and maintain term/document statistics.

## Branch

`feature/indexer-core`

## Deliverables

- term postings
- term frequency
- document frequency
- word positions
- document metadata
- corpus metadata

## Suggested Commits

### Commit 1
**Message:** `feat: add inverted index data model`

Implement the core in-memory structure:

- `meta`
- `documents`
- `terms`

### Commit 2
**Message:** `feat: add document indexing logic with term frequencies`

Index one parsed document into the structure.

### Commit 3
**Message:** `feat: store positional postings and document statistics`

Track:

- positions
- document length
- document frequency

### Commit 4
**Message:** `test: add unit tests for inverted index updates`

Test:

- first occurrence of term
- repeated term in one document
- same term across multiple documents
- metadata updates

### Commit 5
**Message:** `refactor: clean index update helpers and add type hints`

Improve readability and safety.

## Exit Criteria

- any parsed document can be added to the index,
- term and document statistics are correct,
- index unit tests pass.

---

# 8. Phase 6 — Build Pipeline Integration

## Goal

Connect crawler, parser, and indexer into one `build` pipeline.

## Branch

`feature/build-pipeline`

## Deliverables

- end-to-end build logic
- index creation from live crawl
- crawl summary output

## Suggested Commits

### Commit 1
**Message:** `feat: connect crawler output to parser and indexer`

Wire modules together for one document flow.

### Commit 2
**Message:** `feat: implement full build command pipeline`

Integrate with CLI `build` command.

### Commit 3
**Message:** `test: add integration test for build pipeline with mocked pages`

Test end-to-end flow without live network dependency.

### Commit 4
**Message:** `refactor: add build progress messages and summary output`

Improve usability for demo and debugging.

## Exit Criteria

- `build` creates an in-memory index from crawled pages,
- output is understandable,
- pipeline works cleanly through the CLI.

---

# 9. Phase 7 — Storage Layer

## Goal

Persist the index to disk and load it back correctly.

## Branch

`feature/storage-load-save`

## Deliverables

- JSON serialisation
- JSON deserialisation
- file existence checks
- load/save error handling

## Suggested Commits

### Commit 1
**Message:** `feat: add JSON save functionality for inverted index`

Write index to `data/index.json`.

### Commit 2
**Message:** `feat: add JSON load functionality for inverted index`

Reconstruct index in memory.

### Commit 3
**Message:** `test: add storage round-trip tests for save and load`

Test:

- saved then loaded index equality
- missing file handling
- malformed JSON handling

### Commit 4
**Message:** `refactor: improve storage validation and user messages`

Polish file handling and CLI feedback.

## Exit Criteria

- `build` can save the index,
- `load` restores it correctly,
- storage failures are handled cleanly.

---

# 10. Phase 8 — Search Commands

## Goal

Implement `print` and `find` against the loaded index.

## Branch

`feature/search-print-find`

## Deliverables

- `print <word>`
- `find <query>`
- case-insensitive lookup
- AND semantics for multi-word search
- deterministic result formatting

## Suggested Commits

### Commit 1
**Message:** `feat: add single-term index lookup for print command`

Implement lookup and formatted output.

### Commit 2
**Message:** `feat: add multi-term AND search for find command`

Return only documents containing all terms.

### Commit 3
**Message:** `feat: add deterministic search result ordering`

Sort results by a stable rule.

### Commit 4
**Message:** `test: add search tests for print and find commands`

Test:

- existing term
- missing term
- single-word find
- multi-word AND query
- case-insensitive behaviour

### Commit 5
**Message:** `refactor: improve search output formatting and edge-case handling`

Polish UX.

## Exit Criteria

- `print` works,
- `find` works for single and multi-word queries,
- results are stable and readable,
- missing terms and empty input are handled properly.

---

# 11. Phase 9 — Edge Cases and Hardening

## Goal

Strengthen robustness to meet higher grade-band expectations.

## Branch

`feature/testing-integration`

## Deliverables

- stronger validation
- integration tests
- defensive handling of bad inputs and failures

## Suggested Commits

### Commit 1
**Message:** `test: add integration tests for build load print and find workflow`

Test a realistic user flow.

### Commit 2
**Message:** `test: add edge-case coverage for empty queries and malformed data`

Test:

- `print` with no term
- `find` with empty query
- load without index file
- malformed stored index

### Commit 3
**Message:** `refactor: add defensive checks across CLI and storage layers`

Harden the system.

### Commit 4
**Message:** `chore: configure coverage reporting for pytest`

Add coverage command or config.

## Exit Criteria

- baseline system is robust,
- integration tests exist,
- coverage is strong,
- coursework core is submission-ready.

---

# 12. Phase 10 — Documentation and Demo Readiness

## Goal

Prepare the repo for marking and video demonstration.

## Branch

`feature/readme-demo`

## Deliverables

- strong `README.md`
- usage examples
- setup instructions
- testing instructions
- architecture summary
- demo checklist

## Suggested Commits

### Commit 1
**Message:** `docs: expand README with installation and usage instructions`

Add:

- setup
- running the CLI
- command examples

### Commit 2
**Message:** `docs: add testing instructions and project structure overview`

Add:

- how to run tests
- architecture explanation

### Commit 3
**Message:** `docs: add demo checklist and AI usage notes scaffold`

Prepare for final video and reflection.

## Exit Criteria

- repo is easy to run,
- documentation is marker-friendly,
- demo prep has started.

---

# 13. Phase 11 — Advanced Features (Only After Core Is Solid)

These features should be added one at a time, each on a separate feature branch.

Do **not** start them until the baseline tool is complete and tested.

---

# 14. Advanced Feature A — TF-IDF Ranking

## Branch

`feature/ranking-tfidf`

## Goal

Replace arbitrary ordering with relevance-based ranking.

## Suggested Commits

### Commit 1
**Message:** `feat: add inverse document frequency calculations`

### Commit 2
**Message:** `feat: score search results using tf-idf style ranking`

### Commit 3
**Message:** `test: add ranking tests for result ordering`

### Commit 4
**Message:** `refactor: document ranking logic and score formatting`

## Exit Criteria

- ranked results work,
- ranking is explainable in demo,
- tests verify ordering behaviour.

---

# 15. Advanced Feature B — Phrase Search

## Branch

`feature/phrase-search`

## Goal

Support exact phrase queries using positional postings.

Example:

`find "good friends"`

## Suggested Commits

### Commit 1
**Message:** `feat: add quoted query parsing for phrase search`

### Commit 2
**Message:** `feat: implement positional phrase matching`

### Commit 3
**Message:** `test: add phrase search tests using positional index data`

### Commit 4
**Message:** `refactor: unify term and phrase query evaluation paths`

## Exit Criteria

- quoted phrase search works,
- positional logic is correct,
- explanation remains simple enough for the video.

---

# 16. Advanced Feature C — Query Suggestions

## Branch

`feature/query-suggestions`

## Goal

Suggest close indexed terms for misspelled words.

## Suggested Commits

### Commit 1
**Message:** `feat: add edit-distance helper for query suggestions`

### Commit 2
**Message:** `feat: suggest nearest indexed term for missing words`

### Commit 3
**Message:** `test: add suggestion tests for misspelled queries`

## Exit Criteria

- missing-word suggestions work,
- feature is optional and non-disruptive.

---

# 17. Advanced Feature D — Crawl Statistics Report

## Branch

`feature/crawl-report`

## Goal

Generate useful crawl and index summary data.

## Suggested Commits

### Commit 1
**Message:** `feat: collect crawl statistics during build process`

### Commit 2
**Message:** `feat: print crawl summary after successful build`

### Commit 3
**Message:** `test: add coverage for crawl statistics generation`

## Exit Criteria

- summary stats are accurate,
- useful for demo and README.

---

# 18. Advanced Feature E — Smarter Tokenisation

## Branch

`feature/tokenisation-enhancements`

## Goal

Improve word handling for contractions and hyphenated terms.

## Suggested Commits

### Commit 1
**Message:** `feat: preserve apostrophes in supported token patterns`

### Commit 2
**Message:** `feat: improve handling of hyphenated words`

### Commit 3
**Message:** `test: add tokenisation tests for contractions and hyphenated input`

## Exit Criteria

- improvements are demonstrable,
- behaviour remains deterministic.

---

# 19. Recommended Milestone Order for Branches

Recommended order to actually execute:

1. `feature/project-scaffold`
2. `feature/cli-shell`
3. `feature/parser-normalisation`
4. `feature/crawler-core`
5. `feature/indexer-core`
6. `feature/build-pipeline`
7. `feature/storage-load-save`
8. `feature/search-print-find`
9. `feature/testing-integration`
10. `feature/readme-demo`

Only then:

11. `feature/ranking-tfidf`
12. `feature/phrase-search`
13. `feature/query-suggestions`
14. `feature/crawl-report`
15. `feature/tokenisation-enhancements`

---

# 20. Definition of Roadmap Completion

The roadmap is complete when:

- all baseline coursework requirements are implemented,
- each core feature was developed on its own branch,
- commits remain small and understandable,
- tests cover the core pipeline,
- repository documentation is complete,
- advanced features were added only after the baseline was stable.

---

# 21. Suggested Working Pattern With an Agent

For each branch:

1. give the agent the relevant section of `SPECIFICATION.md`,
2. give it the matching phase from `ROADMAP.md`,
3. ask for implementation of only that phase,
4. require tests in the same branch,
5. review and correct before merge.

Recommended prompt pattern:

```text
Read SPECIFICATION.md and ROADMAP.md.

Implement only Phase X on the current branch.
Do not implement future phases.
Keep changes small and modular.
Add or update tests for the feature.
Do not change unrelated files.
```

This will make the agent much more reliable and keep the codebase under control.
