def _render_results(results: list[PullResult]) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Name")
    table.add_column("ID")
    table.add_column("File")
    table.add_column("Status")

    status_style = {
        "unchanged": ("dim", "UNCHANGED"),
        "updated": ("yellow", "UPDATED"),
        "created": ("green", "CREATED"),
        "error": ("red", "ERROR"),
    }

    for r in results:
        color, label = status_style.get(r.status, ("white", r.status.upper()))
        if r.error:
            label += f": {r.error}"
        table.add_row(r.flow_name, str(r.flow_id), str(r.path), f"[{color}]{label}[/{color}]")

    ok_console.print()
    ok_console.print(table)

    errors = [r for r in results if not r.ok]
    n_changed = sum(1 for r in results if r.status in ("created", "updated"))
    n_unchanged = sum(1 for r in results if r.status == "unchanged")
    if errors:
        console.print(f"\n[red]{len(errors)} pull(s) failed.[/red]")
    else:
        parts = []
        if n_changed:
            parts.append(f"[green]{n_changed} updated[/green]")
        if n_unchanged:
            parts.append(f"[dim]{n_unchanged} unchanged[/dim]")
        ok_console.print("\n" + ", ".join(parts) + ".")