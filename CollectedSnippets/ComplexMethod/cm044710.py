def filter_by_tag():
    """Show available tags, user picks one, show matching tools."""
    tag_index = _get_all_tags()
    sorted_tags = sorted(tag_index.keys())

    # Show tags in a compact grid
    console.print(Panel(
        "  ".join(f"[bold cyan]{t}[/bold cyan]([dim]{len(tag_index[t])}[/dim])" for t in sorted_tags),
        title="[bold magenta] Available Tags [/bold magenta]",
        border_style="magenta", box=box.ROUNDED, padding=(0, 2),
    ))

    tag = Prompt.ask("[bold cyan]Enter tag[/bold cyan]", default="").strip().lower()
    if not tag or tag not in tag_index:
        if tag:
            console.print(f"[dim]Tag '{tag}' not found.[/dim]")
            Prompt.ask("[dim]Press Enter to return[/dim]", default="")
        return

    matches = tag_index[tag]
    table = Table(
        title=f"Tools tagged '{tag}'",
        box=box.SIMPLE_HEAD, show_lines=True,
    )
    table.add_column("No.", justify="center", style="bold cyan", width=5)
    table.add_column("", width=2)
    table.add_column("Tool", style="bold yellow", min_width=20)
    table.add_column("Category", style="magenta", min_width=15)

    for i, (tool, cat) in enumerate(matches, start=1):
        status = "[green]✔[/green]" if tool.is_installed else "[dim]✘[/dim]"
        table.add_row(str(i), status, tool.TITLE, cat)

    table.add_row("99", "", "Back to main menu", "")
    console.print(table)

    raw = Prompt.ask("[bold cyan]>[/bold cyan]", default="").strip()
    if not raw or raw == "99":
        return
    try:
        idx = int(raw)
    except ValueError:
        return
    if 1 <= idx <= len(matches):
        tool, cat = matches[idx - 1]
        tool.show_options()