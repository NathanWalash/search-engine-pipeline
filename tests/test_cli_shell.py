"""Tests for CLI command parsing and dispatch behaviour."""

import pytest

from src.main import handle_command, parse_command


def test_parse_command_normalises_case() -> None:
    command, args = parse_command("BuIlD")
    assert command == "build"
    assert args == []


def test_parse_command_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="command cannot be empty"):
        parse_command("   ")


def test_handle_build_returns_placeholder_message() -> None:
    message, should_exit = handle_command("build")
    assert message == "Build requested. Pipeline not implemented yet."
    assert should_exit is False


def test_handle_load_returns_placeholder_message() -> None:
    message, should_exit = handle_command("load")
    assert message == "Load requested. Storage layer not implemented yet."
    assert should_exit is False


def test_handle_print_requires_one_word() -> None:
    with pytest.raises(ValueError, match="word required"):
        handle_command("print")


def test_handle_print_rejects_multiple_words() -> None:
    with pytest.raises(ValueError, match="exactly one word"):
        handle_command("print one two")


def test_handle_find_rejects_empty_query() -> None:
    with pytest.raises(ValueError, match="query cannot be empty"):
        handle_command("find")


def test_handle_find_accepts_multiword_query() -> None:
    message, should_exit = handle_command("find good friends")
    assert message == "Find requested for 'good friends'."
    assert should_exit is False


def test_handle_exit_sets_exit_state() -> None:
    message, should_exit = handle_command("exit")
    assert message == "Exiting search shell."
    assert should_exit is True


def test_handle_unknown_command_errors() -> None:
    with pytest.raises(ValueError, match="unknown command"):
        handle_command("unknown")
