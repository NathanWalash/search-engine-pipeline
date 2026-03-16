"""Utilities for extracting plain text from HTML documents."""

from html.parser import HTMLParser
import re


class _TextExtractor(HTMLParser):
    """Small HTML-to-text fallback when BeautifulSoup is unavailable."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
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
        from bs4 import BeautifulSoup  # type: ignore
    except ModuleNotFoundError:
        return _extract_text_with_stdlib(html)

    soup = BeautifulSoup(html, "html.parser")
    for tag_name in ("script", "style", "noscript"):
        for tag in soup.find_all(tag_name):
            tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def tokenize(text: str) -> list[str]:
    """Split text into lowercase word tokens with punctuation removed."""
    return re.findall(r"[a-z0-9]+", text.lower())


def tokenize_with_positions(text: str) -> list[tuple[str, int]]:
    """Split text into lowercase tokens and include each token position."""
    return [(token, index) for index, token in enumerate(tokenize(text))]


def extract_tokens_from_html(html: str) -> list[str]:
    """Extract and tokenize visible text content from raw HTML."""
    return tokenize(extract_text(html))


def extract_tokens_with_positions_from_html(
    html: str,
) -> list[tuple[str, int]]:
    """Extract text from HTML and return token-position pairs."""
    return tokenize_with_positions(extract_text(html))
