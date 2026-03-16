"""Unit tests for parser extraction and normalisation behaviour."""

from src.parser import (
    extract_text,
    extract_tokens_from_html,
    extract_tokens_with_positions_from_html,
    tokenize,
    tokenize_with_positions,
)


def test_extract_text_ignores_script_and_style_content() -> None:
    html = """
    <html>
        <head>
            <style>.x { color: red; }</style>
            <script>console.log("hidden")</script>
        </head>
        <body>
            <h1>Hello</h1>
            <p>World</p>
        </body>
    </html>
    """

    text = extract_text(html)
    assert text == "Hello World"


def test_tokenize_lowercases_and_strips_punctuation() -> None:
    text = "Friend, GOOD! truth... don't-stop 123"
    assert tokenize(text) == ["friend", "good", "truth", "don", "t", "stop", "123"]


def test_extract_tokens_from_empty_html_returns_empty_list() -> None:
    assert extract_tokens_from_html("<html><body>   </body></html>") == []


def test_tokenize_preserves_repeated_words() -> None:
    assert tokenize("Echo echo ECHO") == ["echo", "echo", "echo"]


def test_tokenize_with_positions_tracks_token_order() -> None:
    assert tokenize_with_positions("Alpha beta alpha") == [
        ("alpha", 0),
        ("beta", 1),
        ("alpha", 2),
    ]


def test_extract_tokens_with_positions_from_html() -> None:
    html = "<p>Good friends make good times.</p>"
    assert extract_tokens_with_positions_from_html(html) == [
        ("good", 0),
        ("friends", 1),
        ("make", 2),
        ("good", 3),
        ("times", 4),
    ]
