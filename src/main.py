"""CLI entry point for the search engine tool."""

from typing import Sequence

PROMPT = "search> "
HELP_TEXT = (
    "Available commands:\n"
    "  build\n"
    "  load\n"
    "  print <word>\n"
    "  find <query>\n"
    "  help\n"
    "  exit"
)


def parse_command(raw_command: str) -> tuple[str, list[str]]:
    """Parse user input into a normalised command and argument list."""
    command_line = raw_command.strip()
    if not command_line:
        raise ValueError("Error: command cannot be empty")

    parts = command_line.split()
    return parts[0].lower(), parts[1:]


def _ensure_no_arguments(command: str, args: Sequence[str]) -> None:
    if args:
        raise ValueError(f"Error: '{command}' does not take arguments")


def dispatch_command(command: str, args: Sequence[str]) -> tuple[str, bool]:
    """Return a placeholder response for the given command."""
    if command == "help":
        _ensure_no_arguments(command, args)
        return HELP_TEXT, False

    if command == "exit":
        _ensure_no_arguments(command, args)
        return "Exiting search shell.", True

    if command == "build":
        _ensure_no_arguments(command, args)
        return "Build requested. Pipeline not implemented yet.", False

    if command == "load":
        _ensure_no_arguments(command, args)
        return "Load requested. Storage layer not implemented yet.", False

    if command == "print":
        if not args:
            raise ValueError("Error: word required")
        if len(args) > 1:
            raise ValueError("Error: print expects exactly one word")
        return f"Print requested for '{args[0]}'.", False

    if command == "find":
        if not args:
            raise ValueError("Error: query cannot be empty")
        query = " ".join(args)
        return f"Find requested for '{query}'.", False

    raise ValueError(
        f"Error: unknown command '{command}'. Type 'help' for usage."
    )


def handle_command(raw_command: str) -> tuple[str, bool]:
    """Parse and dispatch user input, returning message and exit state."""
    command, args = parse_command(raw_command)
    return dispatch_command(command, args)


def run_shell() -> None:
    """Run an interactive command loop."""
    print("Search Engine CLI")
    print("Type 'help' for available commands.")

    while True:
        try:
            raw_command = input(PROMPT)
        except EOFError:
            print("Exiting search shell.")
            break
        except KeyboardInterrupt:
            print("\nExiting search shell.")
            break

        try:
            message, should_exit = handle_command(raw_command)
        except ValueError as error:
            print(error)
            continue

        print(message)
        if should_exit:
            break


def main() -> None:
    """Run the command-line interface."""
    run_shell()


if __name__ == "__main__":
    main()
