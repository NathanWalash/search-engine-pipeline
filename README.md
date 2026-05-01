# Search Engine Pipeline

> A command-line search engine that crawls, indexes, and queries [`quotes.toscrape.com`](https://quotes.toscrape.com/) — COMP3011 Coursework 2.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Tests](https://img.shields.io/badge/tests-186%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)
![Type checked](https://img.shields.io/badge/type--checked-mypy%20strict-blue)

---

## Overview

The tool crawls every page of the target website using a polite BFS crawler, builds an inverted index storing word frequencies and positions, persists the index to disk, and exposes a command-line shell for querying it.

**Core commands:** `build` · `load` · `print` · `find`

**Advanced features:** TF-IDF ranking · BM25 ranking · proximity bonus · result snippets · phrase search · query suggestions · incremental reindex · benchmarking

---

## Quick Start

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Launch the shell
python -m src.main
```

```text
Search Engine CLI
Type 'help' for available commands.
search> build
search> find good friends
search> print indifference
search> exit
```

---

## Installation

**Requirements:** Python 3.11 or 3.12, pip

```bash
python -m pip install -r requirements.txt
```

**Dependencies:**

| Package | Purpose |
|---|---|
| `requests` | HTTP fetching |
| `beautifulsoup4` | HTML parsing |
| `pytest` / `pytest-cov` | Test runner and coverage |
| `ruff` | Linting |
| `mypy` | Static type checking |

---

## Commands

### `build`

Crawls the site, builds the inverted index, and saves it to `data/index.json`.
Enforces a **6-second politeness delay** between requests by default.

```text
search> build
search> build --incremental
```

Incremental mode reuses unchanged documents from a previously loaded index,
only re-parsing pages whose HTML content has changed.

Live progress is printed per page:
```text
Build: crawled 12 page(s) (last: https://quotes.toscrape.com/page/2/)
```

After completion, a crawl report is shown:
```text
Pages crawled: 214  |  Unique terms: 4570  |  Duration: 21.4s
```

> **Local testing only:** override the delay via environment variable before launching:
> ```powershell
> $env:SEARCH_POLITENESS_SECONDS = "1.0"
> python -m src.main
> ```

---

### `load`

Loads a previously built index from `data/index.json`.

```text
search> load
```

The compiled `data/index.json` is committed to the repository for submission
as required by the coursework brief.

---

### `print <word>`

Prints the inverted index entry for a single word: document frequency,
and per-document term frequency and token positions.

```text
search> print good
search> print indifference
```

If the word is not in the index, the closest match is suggested:
```text
Word not found in index
Did you mean: indifferent?
```

---

### `find <query>`

Runs a case-insensitive AND search. Returns ranked results with URLs and scores.

```text
search> find indifference
search> find good friends
search> find "good friends"
search> find --rank bm25 good friends
search> find --proximity-bonus on good friends
search> find --snippets on good friends
```

| Flag | Values | Default | Effect |
|---|---|---|---|
| `--rank` | `tfidf` \| `bm25` | `tfidf` | Ranking algorithm |
| `--proximity-bonus` | `on` \| `off` | `off` | Boost results where query terms appear close together |
| `--snippets` | `on` \| `off` | `off` | Show a context window with matched terms highlighted in `[]` |

Quoted phrases use positional matching — `"good friends"` only matches pages where the words appear consecutively.

If no results are found, spelling suggestions are shown:
```text
No matching pages found.
Did you mean: indifference?
```

---

### `benchmark [--runs N]`

Measures build, incremental reindex, load, and query timings over N repeated runs (default: 5).

```text
search> benchmark
search> benchmark --runs 10
```

Reports include corpus stats, timing breakdowns, and speedup ratios.
See [`docs/BENCHMARK_RESULTS.md`](docs/BENCHMARK_RESULTS.md) for a recorded snapshot.

---

## Tokenisation

| Rule | Example |
|---|---|
| Lowercase all text | `Good` → `good` |
| Preserve internal apostrophes | `don't` stays `don't` |
| Preserve hyphenated terms | `well-known` stays `well-known` |
| Also index split parts | `well-known` also indexes `well`, `known` |
| Strip leading/trailing punctuation | `"hello"` → `hello` |

This **preserve + split** strategy means queries using `well-known`, `well known`,
or just `known` all match hyphenated content.

---

## Testing

```bash
# Full suite with coverage
python -m pytest

# Concise output
python -m pytest -q

# Lint
python -m ruff check src tests

# Type checking
python -m mypy src
```

Coverage is enforced at **95% minimum** via `pytest.ini`. Current coverage: **99.16%** across 186 tests.

Test organisation:

| File | Coverage area |
|---|---|
| `test_crawler.py` | Fetch, BFS traversal, politeness, error handling |
| `test_parser.py` | HTML extraction, tokenisation, hyphen strategy |
| `test_indexer.py` | Document/term indexing, statistics |
| `test_storage.py` | JSON save/load, schema validation |
| `test_search.py` | Term lookup, AND queries, ranking, phrases, snippets |
| `test_ranking.py` | TF-IDF, BM25, proximity signal |
| `test_build_pipeline.py` | Full pipeline, incremental reindex |
| `test_integration_workflow.py` | End-to-end CLI workflow |
| `test_cli_shell.py` | Command parsing, dispatch, error handling |
| `test_benchmarking.py` | Benchmark metrics and formatting |
| `test_edge_cases.py` | Empty queries, missing index, malformed input |

---

## Architecture

```text
build command
  └─ crawler.py       BFS crawl with 6s politeness window
  └─ parser.py        HTML → text → tokens + positions
  └─ indexer.py       Inverted index (term → {doc → {tf, positions}})
  └─ storage.py       JSON serialisation / deserialisation

find command
  └─ search.py        AND intersection, phrase matching, snippets
  └─ ranking.py       TF-IDF / BM25 scoring, proximity bonus
```

**Key data structure:** the inverted index maps each term to a `TermRecord`
containing document frequency and a postings dict keyed by `document_id`
for O(1) lookup during scoring. Each posting stores term frequency and a
list of token positions enabling phrase matching.

**AND intersection optimisation:** query terms are sorted by ascending
document frequency before intersection — rarest terms first — so the
candidate set shrinks as early as possible, short-circuiting before
common terms are processed.

---

## Research References

Ranking and query processing design is grounded in standard IR literature:

- Robertson, S. and Zaragoza, H. (2009). *The Probabilistic Relevance Framework: BM25 and Beyond.* https://doi.org/10.1561/1500000019
- Robertson, S. E. et al. (1994). *Okapi at TREC-3.* https://pages.nist.gov/trec-browser/trec3/proceedings
- Manning, C. D., Raghavan, P. and Schütze, H. (2008). *Introduction to Information Retrieval* — TF-IDF: https://nlp.stanford.edu/IR-book/html/htmledition/tf-idf-weighting-1.html
- Manning et al. (2008). *Introduction to Information Retrieval* — Boolean intersection ordering: https://nlp.stanford.edu/IR-book/html/htmledition/processing-boolean-queries-1.html
- Manning et al. (2008). *Introduction to Information Retrieval* — Positional indexes and phrase queries: https://nlp.stanford.edu/IR-book/html/htmledition/positional-indexes-1.html

---

## Project Layout

```
search-engine-pipeline/
├── src/
│   ├── main.py              CLI shell and command dispatch
│   ├── crawler.py           HTTP fetching, politeness, BFS traversal
│   ├── parser.py            HTML text extraction and tokenisation
│   ├── indexer.py           Inverted index data structures
│   ├── build_pipeline.py    Crawl → parse → index orchestration
│   ├── storage.py           JSON save/load with schema validation
│   ├── search.py            print/find query logic and output
│   ├── ranking.py           TF-IDF, BM25, proximity scoring
│   └── benchmarking.py      Performance measurement harness
├── tests/                   186 tests, 99.16% coverage
├── data/
│   └── index.json           Compiled index (committed for submission)
├── docs/
│   ├── SPECIFICATION.md
│   ├── CORE_ROADMAP.md
│   ├── ADVANCED_ROADMAP.md
│   ├── BENCHMARK_RESULTS.md
│   ├── RELEASE_PLAN.md
│   ├── GIT_WORKFLOW_EVIDENCE.md
│   └── SUBMISSION_CHECKLIST.md
├── .github/workflows/ci.yml  CI: lint → typecheck → tests
├── requirements.txt
└── README.md
```

---

## Demo Checklist

- [ ] `build` — confirm crawl progress and index save path
- [ ] `load` — confirm index loads from `data/index.json`
- [ ] `print <word>` — existing term and missing term (suggestion shown)
- [ ] `find <single term>` — basic result list
- [ ] `find <multi-term>` — AND semantics demonstrated
- [ ] `find "<phrase>"` — quoted phrase search
- [ ] `find --rank bm25` — ranking mode switch
- [ ] `find --proximity-bonus on` — proximity bonus
- [ ] `find --snippets on` — context snippets
- [ ] Empty `find` — graceful error
- [ ] `benchmark --runs 3` — timing output
- [ ] `python -m pytest -q` — test suite passing
- [ ] Git log — incremental branch-based development history

---

## GenAI Usage Notes

Fill this before recording so the reflection stays specific and concise.

```
GenAI tools used:
- Tool:
- Purpose:

Example where GenAI helped:
- Task:
- Suggested output:
- What I kept:
- What I changed and why:

Example where GenAI hindered or was incorrect:
- Task:
- Problem in output:
- How I detected it:
- Fix I applied:

Impact on learning and workflow:
- Time saved:
- Concepts learned:
- Debugging effort:
- What I would do differently next time:
```
