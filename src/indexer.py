"""In-memory inverted index data structures."""

from dataclasses import dataclass, field
from typing import Any, Sequence

TokenPosition = tuple[str, int]


@dataclass
class DocumentRecord:
    """Document-level metadata tracked by the index."""

    url: str
    length: int = 0
    text: str = ""
    content_hash: str = ""


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

    def _register_document(
        self,
        *,
        document_id: str,
        url: str,
        token_count: int,
        text: str = "",
        content_hash: str = "",
    ) -> None:
        if document_id in self.documents:
            raise ValueError(f"Document '{document_id}' already indexed")

        self.documents[document_id] = DocumentRecord(
            url=url,
            length=token_count,
            text=text,
            content_hash=content_hash,
        )
        self.meta["page_count"] += 1
        self.meta["token_count"] += token_count

    def _group_positions(
        self,
        token_positions: Sequence[TokenPosition],
    ) -> dict[str, list[int]]:
        grouped: dict[str, list[int]] = {}
        for term, position in token_positions:
            grouped.setdefault(term, []).append(position)
        return grouped

    def add_document(
        self,
        *,
        document_id: str,
        url: str,
        token_positions: Sequence[TokenPosition],
        text: str = "",
        content_hash: str = "",
    ) -> None:
        """Index one document using positional token postings."""
        self._register_document(
            document_id=document_id,
            url=url,
            token_count=len(token_positions),
            text=text,
            content_hash=content_hash,
        )

        positions_by_term = self._group_positions(token_positions)
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
        text: str = "",
        content_hash: str = "",
    ) -> None:
        """Index one document from raw tokens, inferring token positions."""
        token_positions: list[TokenPosition] = [
            (term, position) for position, term in enumerate(tokens)
        ]
        self.add_document(
            document_id=document_id,
            url=url,
            token_positions=token_positions,
            text=text,
            content_hash=content_hash,
        )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation of the index."""
        return {
            "meta": dict(self.meta),
            "documents": {
                document_id: (
                    {
                        "url": record.url,
                        "length": record.length,
                        "text": record.text,
                        "content_hash": record.content_hash,
                    }
                    if record.content_hash
                    else {
                        "url": record.url,
                        "length": record.length,
                        "text": record.text,
                    }
                )
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

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "InvertedIndex":
        """Construct an index instance from serialized dict data."""
        index = cls()

        meta = raw.get("meta", {})
        index.meta = {
            "page_count": int(meta.get("page_count", 0)),
            "token_count": int(meta.get("token_count", 0)),
        }

        for document_id, document_raw in raw.get("documents", {}).items():
            index.documents[document_id] = DocumentRecord(
                url=str(document_raw.get("url", "")),
                length=int(document_raw.get("length", 0)),
                text=str(document_raw.get("text", "")),
                content_hash=str(document_raw.get("content_hash", "")),
            )

        for term, term_raw in raw.get("terms", {}).items():
            postings: dict[str, PostingRecord] = {}
            for document_id, posting_raw in term_raw.get("postings", {}).items():
                postings[document_id] = PostingRecord(
                    term_frequency=int(posting_raw.get("term_frequency", 0)),
                    positions=[int(position) for position in posting_raw.get("positions", [])],
                )

            document_frequency = int(term_raw.get("document_frequency", len(postings)))
            index.terms[term] = TermRecord(
                document_frequency=document_frequency,
                postings=postings,
            )

        return index


def create_inverted_index() -> InvertedIndex:
    """Create a new empty inverted index instance."""
    return InvertedIndex()
