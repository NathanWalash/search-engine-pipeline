
# COMP3011 Coursework 2 — Search Engine Tool
## System Specification

## 1. Project Overview

This project implements a **command-line search engine tool** for the website:

https://quotes.toscrape.com/

The tool must:

- Crawl the pages of the target website
- Build an inverted index of all words found on those pages
- Store statistics about word occurrences
- Allow the user to search for words or phrases via a command-line interface

The implementation will be written in **Python** and structured as a modular system consisting of crawler, parser, indexer, storage, and search components.

---

# 2. Coursework Requirements

## 2.1 Core Functional Requirements

The tool must implement the following commands:

### build

Crawls the website, builds the inverted index, and saves the index to disk.

Example:

> build

### load

Loads a previously saved index from disk.

Example:

> load

### print <word>

Prints the inverted index entry for a specific word.

Example:

> print nonsense

### find <query>

Returns pages that contain the specified query terms.

Example:

> find good friends

Multi-word queries must be supported.

---

# 3. Technical Constraints

The implementation must follow these rules:

### Politeness Window

The crawler must wait **at least 6 seconds between HTTP requests**.

### Case Sensitivity

Search must be **case insensitive**.

Example:

"Good" == "good"

### Index Statistics

The inverted index must store statistics including:

- Term frequency per page
- Word positions within the page

### Language

The tool must be implemented in **Python**.

Recommended libraries:

- requests (HTTP requests)
- BeautifulSoup (HTML parsing)

---

# 4. System Architecture

The system will follow a modular pipeline architecture.

Crawler → Parser → Indexer → Storage → Query Engine

```
CLI
 │
 ├── Command Dispatcher
 │
 ├── Build Pipeline
 │      ├── crawler.py
 │      ├── parser.py
 │      ├── indexer.py
 │      └── storage.py
 │
 └── Query Pipeline
        ├── search.py
        └── ranking.py
```

---

# 5. Repository Structure

The project repository should follow this structure:

```
repository/
│
├── src/
│   ├── crawler.py
│   ├── parser.py
│   ├── indexer.py
│   ├── storage.py
│   ├── search.py
│   └── main.py
│
├── tests/
│   ├── test_crawler.py
│   ├── test_indexer.py
│   └── test_search.py
│
├── data/
│   └── index.json
│
├── requirements.txt
├── README.md
└── SPECIFICATION.md
```

---

# 6. Crawling Specification

## Scope

Crawler must only visit pages inside:

quotes.toscrape.com

## Crawling Strategy

Use **Breadth First Search (BFS)** traversal.

Steps:

1. Start from root page
2. Extract all internal links
3. Add unseen links to crawl queue
4. Continue until no new pages exist

## Duplicate Handling

Maintain a **visited set** to prevent revisiting URLs.

## Error Handling

Crawler must handle:

- network errors
- timeouts
- HTTP errors
- malformed HTML

Crawler failures must not crash the entire build process.

---

# 7. Text Processing Rules

## Tokenisation

Words must be extracted from page text using these rules:

- convert to lowercase
- remove punctuation
- split on whitespace
- ignore empty tokens

## Normalisation

Examples:

"Friend," → "friend"

"Truth." → "truth"

---

# 8. Inverted Index Design

The inverted index maps:

word → documents containing that word

### Example Structure

```
{
  "meta": {
    "page_count": 10,
    "token_count": 4500
  },

  "documents": {
    "doc1": {
      "url": "https://quotes.toscrape.com/page/1/",
      "length": 320
    }
  },

  "terms": {
    "friend": {
      "document_frequency": 3,
      "postings": {
        "doc1": {
          "term_frequency": 2,
          "positions": [14, 51]
        }
      }
    }
  }
}
```

---

# 9. Storage Specification

The inverted index must be saved to disk.

Recommended format:

JSON

Example location:

data/index.json

The `load` command must reconstruct the index in memory.

---

# 10. Query Engine Behaviour

## print command

Displays information about a word.

Output should include:

- document frequency
- list of pages containing the word
- term frequency per page

## find command

Find pages containing the query terms.

Query processing rules:

- queries are case insensitive
- multiple words are treated as **AND queries**
- pages must contain all query words

Example:

```
find good friends
```

Returns pages containing both "good" AND "friends".

---

# 11. Error Handling Requirements

The CLI must gracefully handle:

Empty queries

Example:

```
find
```

Output:

Error: query cannot be empty

Missing arguments

Example:

```
print
```

Output:

Error: word required

Nonexistent words

Example:

```
print banana
```

Output:

Word not found in index

---

# 12. Testing Requirements

Testing is a major assessment component.

The project must include:

Unit tests for:

- crawler
- parser
- indexer
- search engine

Tests should cover:

- valid queries
- invalid queries
- empty queries
- nonexistent words
- case insensitivity
- multi-word search

Target test coverage:

80–90%

---

# 13. Potential Advanced Features

The following enhancements may be implemented for higher marks.

## Ranking Algorithms

TF-IDF ranking

## Phrase Search

Support queries like:

find "good friends"

using positional index data.

## Query Suggestions

Suggest closest indexed word when query word is missing.

Example:

```
find frend
Did you mean: friend?
```

## Stop Word Filtering

Ignore common words such as:

the, is, a, and

## Crawl Statistics

Produce crawl report:

- pages crawled
- unique terms
- crawl duration

## Result Ranking

Sort results by relevance score instead of arbitrary order.

## Improved Tokenisation

Handle:

- apostrophes
- contractions
- hyphenated words

## Compression

Compress index file to reduce storage size.

---

# 14. Non‑Functional Requirements

The system must be:

Reliable

Crawler must not crash due to network errors.

Deterministic

Search results should be reproducible.

Modular

Each component must be independently testable.

Readable

Code should follow Python best practices.

Documented

Every module must include docstrings.

---

# 15. Definition of Done

The system is complete when:

- build command crawls the entire site
- crawler respects the 6 second politeness rule
- inverted index is correctly generated
- index can be saved and loaded
- print command displays index entries
- find command supports multi-word queries
- errors are handled gracefully
- test suite passes
- repository structure matches specification
