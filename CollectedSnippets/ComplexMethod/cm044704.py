def show_options(self, parent=None):
        """Iterative menu loop — no recursion, no stack growth."""
        while True:
            clear_screen()
            self.show_info()

            table = Table(title="Options", box=box.SIMPLE_HEAVY)
            table.add_column("No.", style="bold cyan", justify="center")
            table.add_column("Action", style="bold yellow")

            for index, option in enumerate(self.OPTIONS):
                table.add_row(str(index + 1), option[0])

            if self.PROJECT_URL:
                table.add_row("98", "Open Project Page")
            table.add_row("99", f"Back to {parent.TITLE if parent else 'Main Menu'}")
            console.print(table)
            console.print(
                "  [dim cyan]?[/dim cyan][dim]help  "
                "[/dim][dim cyan]q[/dim cyan][dim]uit  "
                "[/dim][dim cyan]99[/dim cyan][dim] back[/dim]"
            )

            raw = Prompt.ask("[bold cyan]╰─>[/bold cyan]", default="").strip().lower()
            if not raw:
                continue
            if raw in ("?", "help"):
                _show_inline_help()
                continue
            if raw in ("q", "quit", "exit"):
                raise SystemExit(0)

            try:
                choice = int(raw)
            except ValueError:
                console.print("[error]⚠ Enter a number, ? for help, or q to quit.[/error]")
                Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
                continue

            if choice == 99:
                return
            elif choice == 98 and self.PROJECT_URL:
                self.show_project_page()
            elif 1 <= choice <= len(self.OPTIONS):
                try:
                    self.OPTIONS[choice - 1][1]()
                except Exception:
                    console.print_exception(show_locals=True)
                Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            else:
                console.print("[error]⚠ Invalid option.[/error]")