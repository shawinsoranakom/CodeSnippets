def _prompt(message: str, options: list[str]) -> str:
        """Display gate message and prompt for a choice."""
        print("\n  ┌─ Gate ─────────────────────────────────────")
        print(f"  │ {message}")
        print("  │")
        for i, opt in enumerate(options, 1):
            print(f"  │  [{i}] {opt}")
        print("  └────────────────────────────────────────────")

        while True:
            try:
                raw = input(f"  Choose [1-{len(options)}]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return options[-1]  # default to last (usually reject)
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                return options[int(raw) - 1]
            # Also accept the option name directly
            if raw.lower() in [o.lower() for o in options]:
                return next(o for o in options if o.lower() == raw.lower())
            print(f"  Invalid choice. Enter 1-{len(options)} or an option name.")