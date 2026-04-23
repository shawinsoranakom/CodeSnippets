def interact_menu():
    while True:
        try:
            build_menu()
            raw = Prompt.ask(
                "[bold magenta]╰─>[/bold magenta]", default=""
            ).strip()

            if not raw:
                continue

            raw_lower = raw.lower()

            if raw_lower in ("?", "help"):
                show_help()
                continue

            if raw.startswith("/"):
                # Inline search: /subdomain → search immediately
                query = raw[1:].strip()
                search_tools(query=query if query else None)
                continue

            if raw_lower in ("s", "search"):
                search_tools()
                continue

            if raw_lower in ("t", "tag", "tags", "filter"):
                filter_by_tag()
                continue

            if raw_lower in ("r", "rec", "recommend"):
                recommend_tools()
                continue

            if raw_lower in ("q", "quit", "exit"):
                console.print(Panel(
                    "[bold white on magenta]  Goodbye — Come Back Safely  [/bold white on magenta]",
                    box=box.HEAVY, border_style="magenta",
                ))
                break

            try:
                choice = int(raw_lower)
            except ValueError:
                console.print("[red]⚠  Invalid input — enter a number, /query to search, or q to quit.[/red]")
                Prompt.ask("[dim]Press Enter to continue[/dim]", default="")
                continue

            if 1 <= choice <= len(all_tools):
                title, icon, _ = tool_definitions[choice - 1]
                console.print(Panel(
                    f"[bold magenta]{icon}  {title}[/bold magenta]",
                    border_style="magenta", box=box.ROUNDED,
                ))
                try:
                    all_tools[choice - 1].show_options()
                except Exception as e:
                    console.print(Panel(
                        f"[red]Error while opening {title}[/red]\n{e}",
                        border_style="red",
                    ))
                    Prompt.ask("[dim]Press Enter to return to main menu[/dim]", default="")
            else:
                console.print(f"[red]⚠  Choose 1–{len(all_tools)}, ? for help, or q to quit.[/red]")
                Prompt.ask("[dim]Press Enter to continue[/dim]", default="")

        except KeyboardInterrupt:
            console.print("\n[bold red]Interrupted — exiting[/bold red]")
            break