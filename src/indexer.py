"""In-memory inverted index data structures."""

from dataclasses import dataclass, field


@dataclass
class DocumentRecord:
    """Document-level metadata tracked by the index."""

    url: str
    length: int = 0


@dataclass
class PostingRecord:
    """Posting information for one term in one document."""

    term_frequency: int = 0
    positions: list[int] = field(default_factory=list)


@dataclass
class TermRecord:
    """Term-level metadata and postings list."""

    document_frequency: int = 0
    postings: dict[str, PostingRecord] = field(default_factory=dict)


@dataclass
class InvertedIndex:
    """Container for all index metadata, document data, and terms."""

    meta: dict[str, int] = field(
        default_factory=lambda: {
            "page_count": 0,
            "token_count": 0,
        }
    )
    documents: dict[str, DocumentRecord] = field(default_factory=dict)
    terms: dict[str, TermRecord] = field(default_factory=dict)

    def add_document(
        self,
        *,
        document_id: str,
        url: str,
        token_positions: list[tuple[str, int]],
    ) -> None:
        """Index one document using positional token postings."""
        if document_id in self.documents:
            raise ValueError(f"Document '{document_id}' already indexed")

        self.documents[document_id] = DocumentRecord(
            url=url,
            length=len(token_positions),
        )
        self.meta["page_count"] += 1
        self.meta["token_count"] += len(token_positions)

        positions_by_term: dict[str, list[int]] = {}
        for term, position in token_positions:
            positions = positions_by_term.setdefault(term, [])
            positions.append(position)

        for term, positions in positions_by_term.items():
            term_record = self.terms.setdefault(term, TermRecord())
            term_record.postings[document_id] = PostingRecord(
                term_frequency=len(positions),
                positions=list(positions),
            )
            term_record.document_frequency = len(term_record.postings)

    def add_document_terms(
        self,
        *,
        document_id: str,
        url: str,
        tokens: list[str],
    ) -> None:
        """Index one document from raw tokens, inferring token positions."""
        token_positions = [(term, position) for position, term in enumerate(tokens)]
        self.add_document(
            document_id=document_id,
            url=url,
            token_positions=token_positions,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the index."""
        return {
            "meta": dict(self.meta),
            "documents": {
                document_id: {
                    "url": record.url,
                    "length": record.length,
                }
                for document_id, record in self.documents.items()
            },
            "terms": {
                term: {
                    "document_frequency": term_record.document_frequency,
                    "postings": {
                        document_id: {
                            "term_frequency": posting.term_frequency,
                            "positions": list(posting.positions),
                        }
                        for document_id, posting in term_record.postings.items()
                    },
                }
                for term, term_record in self.terms.items()
            },
        }


def create_inverted_index() -> InvertedIndex:
    """Create a new empty inverted index instance."""
    return InvertedIndex()
