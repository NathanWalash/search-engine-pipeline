"""Tests for CLI command parsing and dispatch behaviour."""

import pytest

import src.main as main_module
from src.build_pipeline import BuildResult, BuildSummary
from src.indexer import create_inverted_index
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


def test_handle_help_returns_help_text() -> None:
    message, should_exit = handle_command("help")
    assert "Available commands:" in message
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


def test_handle_print_accepts_one_word() -> None:
    message, should_exit = handle_command("print nonsense")
    assert message == "Print requested for 'nonsense'."
    assert should_exit is False


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


def test_help_rejects_unexpected_arguments() -> None:
    with pytest.raises(ValueError, match="does not take arguments"):
        handle_command("help extra")


def test_run_shell_handles_eof_exit(monkeypatch, capsys) -> None:
    def raise_eof(prompt: str) -> str:
        del prompt
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    main_module.run_shell()
    output = capsys.readouterr().out

    assert "Search Engine CLI" in output
    assert "Exiting search shell." in output


def test_run_shell_handles_keyboard_interrupt(monkeypatch, capsys) -> None:
    def raise_interrupt(prompt: str) -> str:
        del prompt
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raise_interrupt)

    main_module.run_shell()
    output = capsys.readouterr().out

    assert "Search Engine CLI" in output
    assert "Exiting search shell." in output


def test_run_shell_prints_error_then_exits(monkeypatch, capsys) -> None:
    commands = iter(["print", "exit"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(commands))

    main_module.run_shell()
    output = capsys.readouterr().out

    assert "Error: word required" in output
    assert "Exiting search shell." in output


def test_main_calls_run_shell(monkeypatch) -> None:
    called: list[bool] = []

    monkeypatch.setattr(main_module, "run_shell", lambda: called.append(True))
    main_module.main()

    assert called == [True]


def test_handle_build_with_pipeline_updates_context() -> None:
    context = main_module.CLIContext()
    built_index = create_inverted_index()
    built_index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/",
        tokens=["good"],
    )

    def fake_build_pipeline():
        return BuildResult(
            index=built_index,
            pages=[],
            summary=BuildSummary(
                pages_crawled=0,
                unique_terms=1,
                token_count=1,
                duration_seconds=0.4,
            ),
        )

    message, should_exit = handle_command(
        "build",
        context=context,
        build_pipeline=fake_build_pipeline,
    )

    assert "Build complete." in message
    assert "Pages crawled: 0" in message
    assert should_exit is False
    assert context.index is built_index
