"""CLI entry point for the search engine tool."""

PROMPT = "search> "
HELP_TEXT = (
    "Commands: build, load, print <word>, find <query>, help, exit"
)


def run_shell() -> None:
    """Run an interactive command loop."""
    print("Search Engine CLI")
    print("Type 'help' for available commands.")

    while True:
        try:
            raw_command = input(PROMPT).strip()
        except EOFError:
            print("Exiting search shell.")
            break
        except KeyboardInterrupt:
            print("\nExiting search shell.")
            break

        if not raw_command:
            print("Error: command cannot be empty")
            continue

        normalised = raw_command.lower()

        if normalised == "help":
            print(HELP_TEXT)
            continue

        if normalised == "exit":
            print("Exiting search shell.")
            break

        print(f"Error: unknown command '{raw_command}'")


def main() -> None:
    """Run the command-line interface."""
    run_shell()


if __name__ == "__main__":
    main()
