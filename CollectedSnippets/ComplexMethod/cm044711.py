def recommend_tools():
    """Show common tasks, user picks one, show matching tools."""
    table = Table(
        title="What do you want to do?",
        box=box.SIMPLE_HEAD,
    )
    table.add_column("No.", justify="center", style="bold cyan", width=5)
    table.add_column("Task", style="bold yellow")

    tasks = list(_RECOMMENDATIONS.keys())
    for i, task in enumerate(tasks, start=1):
        table.add_row(str(i), task.title())

    table.add_row("99", "Back to main menu")
    console.print(table)

    raw = Prompt.ask("[bold cyan]>[/bold cyan]", default="").strip()
    if not raw or raw == "99":
        return

    try:
        idx = int(raw)
    except ValueError:
        return

    if 1 <= idx <= len(tasks):
        task = tasks[idx - 1]
        tag_names = _RECOMMENDATIONS[task]
        tag_index = _get_all_tags()

        # Collect unique tools across all matching tags
        seen = set()
        matches = []
        for tag in tag_names:
            for tool, cat in tag_index.get(tag, []):
                if id(tool) not in seen:
                    seen.add(id(tool))
                    matches.append((tool, cat))

        if not matches:
            console.print("[dim]No tools found for this task.[/dim]")
            Prompt.ask("[dim]Press Enter to return[/dim]", default="")
            return

        console.print(Panel(
            f"[bold]Recommended tools for: {task.title()}[/bold]",
            border_style="green", box=box.ROUNDED,
        ))

        rtable = Table(box=box.SIMPLE_HEAD, show_lines=True)
        rtable.add_column("No.", justify="center", style="bold cyan", width=5)
        rtable.add_column("", width=2)
        rtable.add_column("Tool", style="bold yellow", min_width=20)
        rtable.add_column("Category", style="magenta")

        for i, (tool, cat) in enumerate(matches, start=1):
            status = "[green]✔[/green]" if tool.is_installed else "[dim]✘[/dim]"
            rtable.add_row(str(i), status, tool.TITLE, cat)

        rtable.add_row("99", "", "Back", "")
        console.print(rtable)

        raw2 = Prompt.ask("[bold cyan]>[/bold cyan]", default="").strip()
        if raw2 and raw2 != "99":
            try:
                ridx = int(raw2)
                if 1 <= ridx <= len(matches):
                    matches[ridx - 1][0].show_options()
            except ValueError:
                pass