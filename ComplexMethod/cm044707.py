def show_options(self, parent=None):
        """Iterative menu loop — no recursion, no stack growth."""
        while True:
            clear_screen()
            self.show_info()

            active = self._active_tools()
            incompatible = self._incompatible_tools()
            archived = self._archived_tools()

            table = Table(title="Available Tools", box=box.SIMPLE_HEAD, show_lines=True)
            table.add_column("No.", justify="center", style="bold cyan", width=6)
            table.add_column("", width=2)  # installed indicator
            table.add_column("Tool", style="bold yellow", min_width=24)
            table.add_column("Description", style="white", overflow="fold")

            for index, tool in enumerate(active, start=1):
                desc = getattr(tool, "DESCRIPTION", "") or "—"
                desc = desc.splitlines()[0] if desc != "—" else "—"
                has_status = hasattr(tool, "is_installed")
                status = ("[green]✔[/green]" if tool.is_installed else "[dim]✘[/dim]") if has_status else ""
                table.add_row(str(index), status, tool.TITLE, desc)

            # Count not-installed tools for "Install All" label (skip sub-collections)
            not_installed = [t for t in active if hasattr(t, "is_installed") and not t.is_installed]
            if not_installed:
                table.add_row(
                    "[bold green]97[/bold green]", "",
                    f"[bold green]Install all ({len(not_installed)} not installed)[/bold green]", "",
                )
            if archived:
                table.add_row("[dim]98[/dim]", "", f"[archived]Archived tools ({len(archived)})[/archived]", "")
            if incompatible:
                console.print(f"[dim]({len(incompatible)} tools hidden — not supported on current OS)[/dim]")

            table.add_row("99", "", f"Back to {parent.TITLE if parent else 'Main Menu'}", "")
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
                continue

            if choice == 99:
                return
            elif choice == 97 and not_installed:
                console.print(Panel(
                    f"[bold]Installing {len(not_installed)} tools...[/bold]",
                    border_style="green", box=box.ROUNDED,
                ))
                for i, tool in enumerate(not_installed, start=1):
                    console.print(f"\n[bold cyan]({i}/{len(not_installed)})[/bold cyan] {tool.TITLE}")
                    try:
                        tool.install()
                    except Exception:
                        console.print(f"[error]✘ Failed: {tool.TITLE}[/error]")
                Prompt.ask("\n[dim]Press Enter to continue[/dim]", default="")
            elif choice == 98 and archived:
                self._show_archived_tools()
            elif 1 <= choice <= len(active):
                try:
                    active[choice - 1].show_options(parent=self)
                except Exception:
                    console.print_exception(show_locals=True)
                    Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
            else:
                console.print("[error]⚠ Invalid option.[/error]")