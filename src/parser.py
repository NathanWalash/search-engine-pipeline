"""Utilities for extracting plain text from HTML documents."""

from dataclasses import dataclass
from html.parser import HTMLParser
import re

# Matches a base alphanumeric token optionally followed by an apostrophe or
# hyphen and more alphanumerics, so "don't" and "well-known" are kept intact.
BASE_TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)*")
TokenPosition = tuple[str, int]


@dataclass(frozen=True)
class ParsedDocument:
    """Represents extracted text and its normalized token forms."""

    text: str
    tokens: list[str]
    token_positions: list[TokenPosition]


class _TextExtractor(HTMLParser):
    """Small HTML-to-text fallback when BeautifulSoup is unavailable."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        # Counter rather than bool so nested script/style tags are handled correctly.
        self._ignore_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in {"script", "style", "noscript"}:
            self._ignore_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignore_depth > 0:
            self._ignore_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignore_depth == 0:
            cleaned = data.strip()
            if cleaned:
                self._parts.append(cleaned)

    def text(self) -> str:
        return " ".join(self._parts)


def _extract_text_with_stdlib(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return parser.text()


def extract_text(html: str) -> str:
    """Extract visible text content from raw HTML."""
    try:
        # Lazy import keeps BeautifulSoup optional; stdlib fallback used if absent.
        from bs4 import BeautifulSoup
    except ModuleNotFoundError:
        return _extract_text_with_stdlib(html)

    soup = BeautifulSoup(html, "html.parser")
    for tag_name in ("script", "style", "noscript"):
        for tag in soup.find_all(tag_name):
            tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def _iter_base_tokens(text: str) -> list[str]:
    """Return normalized base tokens preserving internal apostrophes/hyphens."""
    return [match.group(0) for match in BASE_TOKEN_PATTERN.finditer(text.lower())]


def _expand_token(base_token: str, *, expand_hyphenated: bool) -> list[str]:
    """Return one base token plus optional split components."""
    emitted = [base_token]
    if not expand_hyphenated or "-" not in base_token:
        return emitted

    # "preserve + split" strategy: index "well-known" AND "well"/"known" separately
    # so queries using any of the three forms can still match the document.
    emitted.extend(part for part in base_token.split("-") if part)
    return emitted


def tokenize_with_positions(
    text: str,
    *,
    expand_hyphenated: bool = True,
) -> list[TokenPosition]:
    """Return normalized tokens with base-token positions.

    For hyphenated tokens, canonical and split terms share the same position.
    """
    token_positions: list[TokenPosition] = []
    for base_position, base_token in enumerate(_iter_base_tokens(text)):
        expanded_tokens = _expand_token(
            base_token,
            expand_hyphenated=expand_hyphenated,
        )
        for token in expanded_tokens:
            # All expanded forms of a hyphenated token share the same base position
            # so phrase matching treats them as occupying the same slot.
            token_positions.append((token, base_position))
    return token_positions


def tokenize(
    text: str,
    *,
    expand_hyphenated: bool = True,
) -> list[str]:
    """Return normalized tokens.

    Apostrophes inside words are preserved.
    Hyphenated tokens can emit canonical+split forms.
    """
    return [
        token
        for token, _ in tokenize_with_positions(
            text,
            expand_hyphenated=expand_hyphenated,
        )
    ]


def extract_tokens_from_html(html: str) -> list[str]:
    """Extract visible text from HTML and return normalized tokens."""
    return parse_html(html).tokens


def extract_tokens_with_positions_from_html(
    html: str,
) -> list[TokenPosition]:
    """Extract visible text from HTML and return token-position pairs."""
    return parse_html(html).token_positions


def parse_html(html: str) -> ParsedDocument:
    """Extract text and return all normalized parser outputs together."""
    text = extract_text(html)
    token_positions = tokenize_with_positions(text, expand_hyphenated=True)
    tokens = [token for token, _ in token_positions]
    return ParsedDocument(
        text=text,
        tokens=tokens,
        token_positions=token_positions,
    )
