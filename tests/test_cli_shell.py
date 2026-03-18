"""Tests for CLI command parsing and dispatch behaviour."""

import runpy
from pathlib import Path

import pytest

import src.main as main_module
from src.build_pipeline import BuildResult, BuildSummary
from src.indexer import create_inverted_index
from src.main import handle_command, parse_command
from src.storage import StorageError


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


def test_handle_find_accepts_ranking_flag() -> None:
    message, should_exit = handle_command("find --rank bm25 good friends")
    assert message == "Find requested for 'good friends'."
    assert should_exit is False


def test_handle_find_accepts_equals_ranking_flag() -> None:
    message, should_exit = handle_command("find --rank=bm25 good")
    assert message == "Find requested for 'good'."
    assert should_exit is False


def test_handle_find_accepts_proximity_bonus_flag() -> None:
    message, should_exit = handle_command("find --proximity-bonus on good friends")
    assert message == "Find requested for 'good friends'."
    assert should_exit is False


def test_handle_find_accepts_equals_proximity_bonus_flag() -> None:
    message, should_exit = handle_command("find --proximity-bonus=on good")
    assert message == "Find requested for 'good'."
    assert should_exit is False


def test_handle_find_accepts_snippets_flag() -> None:
    message, should_exit = handle_command("find --snippets on good friends")
    assert message == "Find requested for 'good friends'."
    assert should_exit is False


def test_handle_find_accepts_equals_snippets_flag() -> None:
    message, should_exit = handle_command("find --snippets=on good")
    assert message == "Find requested for 'good'."
    assert should_exit is False


def test_handle_find_rejects_missing_ranking_mode_value() -> None:
    with pytest.raises(ValueError, match="--rank requires one of"):
        handle_command("find --rank")


def test_handle_find_rejects_unsupported_ranking_mode() -> None:
    with pytest.raises(ValueError, match="unsupported ranking mode"):
        handle_command("find --rank madeup good")


def test_handle_find_rejects_missing_proximity_bonus_value() -> None:
    with pytest.raises(ValueError, match="--proximity-bonus requires one of"):
        handle_command("find --proximity-bonus")


def test_handle_find_rejects_unsupported_proximity_bonus_value() -> None:
    with pytest.raises(ValueError, match="unsupported proximity bonus mode"):
        handle_command("find --proximity-bonus maybe good")


def test_handle_find_rejects_missing_snippets_value() -> None:
    with pytest.raises(ValueError, match="--snippets requires one of"):
        handle_command("find --snippets")


def test_handle_find_rejects_unsupported_snippets_value() -> None:
    with pytest.raises(ValueError, match="unsupported snippets mode"):
        handle_command("find --snippets maybe good")


def test_handle_benchmark_returns_placeholder_message() -> None:
    message, should_exit = handle_command("benchmark")
    assert message == "Benchmark requested. Benchmark harness not implemented yet."
    assert should_exit is False


def test_handle_benchmark_accepts_runs_flag_without_context() -> None:
    message, should_exit = handle_command("benchmark --runs 3")
    assert message == "Benchmark requested. Benchmark harness not implemented yet."
    assert should_exit is False


def test_handle_benchmark_with_loaded_index_returns_summary() -> None:
    context = main_module.CLIContext(index=create_inverted_index())
    context.index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["good", "friends"],
        text="Good friends.",
    )
    message, should_exit = handle_command("benchmark --runs=1", context=context)

    assert should_exit is False
    assert "Benchmark summary:" in message
    assert "TF-IDF vs BM25 ratio" in message


def test_handle_benchmark_requires_loaded_index() -> None:
    context = main_module.CLIContext(index=None)
    with pytest.raises(ValueError, match="no index loaded"):
        handle_command("benchmark", context=context)


def test_handle_benchmark_rejects_invalid_runs() -> None:
    with pytest.raises(ValueError, match="benchmark runs must be a positive integer"):
        handle_command("benchmark --runs nope")


def test_handle_benchmark_rejects_invalid_usage() -> None:
    with pytest.raises(ValueError, match="usage: benchmark"):
        handle_command("benchmark nope")


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


def test_handle_build_with_save_function_reports_path() -> None:
    context = main_module.CLIContext()
    built_index = create_inverted_index()

    def fake_build_pipeline():
        return BuildResult(
            index=built_index,
            pages=[],
            summary=BuildSummary(
                pages_crawled=0,
                unique_terms=0,
                token_count=0,
                duration_seconds=0.1,
            ),
        )

    message, _ = handle_command(
        "build",
        context=context,
        build_pipeline=fake_build_pipeline,
        save_index_fn=lambda index: "data/index.json",
    )

    assert "Index saved to: data/index.json" in message
    assert context.index is built_index


def test_handle_build_wraps_save_storage_error() -> None:
    context = main_module.CLIContext()
    built_index = create_inverted_index()

    def fake_build_pipeline():
        return BuildResult(
            index=built_index,
            pages=[],
            summary=BuildSummary(
                pages_crawled=0,
                unique_terms=0,
                token_count=0,
                duration_seconds=0.1,
            ),
        )

    with pytest.raises(ValueError, match="Unable to save index file"):
        handle_command(
            "build",
            context=context,
            build_pipeline=fake_build_pipeline,
            save_index_fn=lambda index: (_ for _ in ()).throw(
                StorageError("Unable to save index file: data/index.json")
            ),
        )


def test_read_politeness_seconds_defaults_to_coursework_value(monkeypatch) -> None:
    monkeypatch.delenv("SEARCH_POLITENESS_SECONDS", raising=False)
    assert main_module._read_politeness_seconds() == 6.0


def test_read_politeness_seconds_allows_override(monkeypatch) -> None:
    monkeypatch.setenv("SEARCH_POLITENESS_SECONDS", "0.75")
    assert main_module._read_politeness_seconds() == 0.75


def test_read_politeness_seconds_rejects_invalid_value(monkeypatch) -> None:
    monkeypatch.setenv("SEARCH_POLITENESS_SECONDS", "abc")
    with pytest.raises(ValueError, match="SEARCH_POLITENESS_SECONDS"):
        main_module._read_politeness_seconds()


def test_read_politeness_seconds_rejects_non_positive_value(monkeypatch) -> None:
    monkeypatch.setenv("SEARCH_POLITENESS_SECONDS", "0")
    with pytest.raises(ValueError, match="greater than 0"):
        main_module._read_politeness_seconds()


def test_format_suggestions_handles_empty_single_and_multiple() -> None:
    assert main_module._format_suggestions({}) == ""
    assert main_module._format_suggestions({"frend": "friend"}) == "Did you mean: friend?"
    rendered = main_module._format_suggestions({"frend": "friend", "godo": "good"})
    assert "Did you mean:" in rendered
    assert "- frend -> friend" in rendered
    assert "- godo -> good" in rendered


def test_handle_load_sets_context_index() -> None:
    context = main_module.CLIContext()
    loaded_index = create_inverted_index()

    message, should_exit = handle_command(
        "load",
        context=context,
        load_index_fn=lambda: (loaded_index, "data/index.json"),
    )

    assert message == "Index loaded from: data/index.json"
    assert should_exit is False
    assert context.index is loaded_index


def test_handle_load_wraps_storage_error() -> None:
    context = main_module.CLIContext()

    with pytest.raises(ValueError, match="Index file not found"):
        handle_command(
            "load",
            context=context,
            load_index_fn=lambda: (_ for _ in ()).throw(
                StorageError("Index file not found: data/index.json")
            ),
        )


def test_handle_find_no_matches_reports_empty_results() -> None:
    context = main_module.CLIContext(index=create_inverted_index())
    context.index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["truth"],
    )

    message, should_exit = handle_command("find banana", context=context)
    assert should_exit is False
    assert message == "No matching pages found."


def test_handle_print_missing_word_reports_suggestion_when_available() -> None:
    context = main_module.CLIContext(index=create_inverted_index())
    context.index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["friend"],
    )

    message, should_exit = handle_command("print frend", context=context)

    assert should_exit is False
    assert message == "Word not found in index\nDid you mean: friend?"


def test_handle_find_missing_word_reports_suggestion_when_available() -> None:
    context = main_module.CLIContext(index=create_inverted_index())
    context.index.add_document_terms(
        document_id="doc1",
        url="https://quotes.toscrape.com/page/1/",
        tokens=["friend"],
    )

    message, should_exit = handle_command("find frend", context=context)

    assert should_exit is False
    assert message == "No matching pages found.\nDid you mean: friend?"


def test_handle_find_rejects_flag_only_query() -> None:
    with pytest.raises(ValueError, match="query cannot be empty"):
        handle_command("find --rank bm25")


def test_handle_benchmark_rejects_non_positive_runs() -> None:
    with pytest.raises(ValueError, match="benchmark runs must be a positive integer"):
        handle_command("benchmark --runs 0")


def test_running_module_main_entrypoint_via_main_guard(monkeypatch, capsys) -> None:
    def raise_eof(prompt: str) -> str:
        del prompt
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    runpy.run_path(str(Path(main_module.__file__)), run_name="__main__")
    output = capsys.readouterr().out

    assert "Search Engine CLI" in output
    assert "Exiting search shell." in output
