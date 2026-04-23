def _render_results(results: list[PushResult], *, dry_run: bool) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("File")
    table.add_column("Name")
    table.add_column("ID")
    table.add_column("Status")
    table.add_column("URL")

    status_colors = {
        "created": "green",
        "updated": "cyan",
        "unchanged": "dim",
        "dry-run": "yellow",
        "error": "red",
    }

    for r in results:
        color = status_colors.get(r.status, "white")
        label = r.status.upper() + (f": {r.error}" if r.error else "")
        url_cell = f"[blue]{r.flow_url}[/blue]" if r.flow_url and r.ok else (r.flow_url or "")
        table.add_row(
            str(r.path),
            r.flow_name,
            str(r.flow_id),
            f"[{color}]{label}[/{color}]",
            url_cell,
        )

    ok_console.print()
    ok_console.print(table)

    errors = [r for r in results if not r.ok]
    if errors:
        console.print(f"\n[red]{len(errors)} push(es) failed.[/red]")
    elif dry_run:
        ok_console.print(f"\n[yellow]{len(results)} flow(s) would be pushed (dry-run).[/yellow]")
    else:
        created = sum(1 for r in results if r.status == "created")
        updated = sum(1 for r in results if r.status == "updated")
        unchanged = sum(1 for r in results if r.status == "unchanged")
        parts = []
        if created:
            parts.append(f"[green]{created} created[/green]")
        if updated:
            parts.append(f"[cyan]{updated} updated[/cyan]")
        if unchanged:
            parts.append(f"[dim]{unchanged} unchanged[/dim]")
        ok_console.print("\n" + ", ".join(parts) + ".")