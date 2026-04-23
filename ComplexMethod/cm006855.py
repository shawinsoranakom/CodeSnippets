def _render_table(statuses: list[FlowStatus], env_label: str) -> None:
    table = Table(
        box=box.SIMPLE,
        show_header=True,
        header_style="bold",
        title=f"Flow status vs [bold]{env_label}[/bold]",
        title_justify="left",
    )
    table.add_column("Flow", min_width=24)
    table.add_column("ID", style="dim", min_width=10)
    table.add_column("File", style="dim")
    table.add_column("Status", min_width=14)

    for s in statuses:
        icon, color, label = _STATUS_STYLE.get(s.status, ("?", "dim", s.status))
        detail_str = f"  [dim]({s.detail})[/dim]" if s.detail else ""
        id_str = str(s.flow_id)[:8] + "…" if s.flow_id else "—"
        file_str = s.path.name if s.path else "—"
        table.add_row(
            s.name,
            id_str,
            file_str,
            f"[{color}]{icon} {label}[/{color}]{detail_str}",
        )

    console.print(table)

    # Summary line
    counts: dict[str, int] = {}
    for s in statuses:
        counts[s.status] = counts.get(s.status, 0) + 1

    parts = []
    for status, (_, color, label) in _STATUS_STYLE.items():
        if counts.get(status):
            parts.append(f"[{color}]{counts[status]} {label}[/{color}]")

    if parts:
        console.print("  " + "  ·  ".join(parts))
        console.print()