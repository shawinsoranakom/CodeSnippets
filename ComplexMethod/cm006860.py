def _collect_flow_files(sources: list[str], dir_path: str | None) -> list[Path]:
    """Resolve the set of flow JSON files to push.

    When neither explicit file paths nor ``--dir`` are given, defaults to
    ``flows/`` — mirroring the behaviour of ``lfx pull``.
    """
    paths: list[Path] = []
    root = _find_project_root()

    # Default to flows/ when nothing is specified, just like lfx pull does.
    effective_dir = dir_path or (None if sources else "flows")

    if effective_dir:
        d = Path(effective_dir)
        _check_path_containment(d, root)
        if not d.is_dir():
            console.print(f"[red]Error:[/red] Directory not found: {d}")
            raise typer.Exit(1)
        paths.extend(sorted(d.glob("*.json")))
        if not paths:
            console.print(f"[yellow]Warning:[/yellow] No *.json files found in {d}")

    for s in sources:
        p = Path(s)
        _check_path_containment(p, root)
        if not p.exists():
            console.print(f"[red]Error:[/red] File not found: {p}")
            raise typer.Exit(1)
        if p.is_dir():
            dir_jsons = sorted(p.glob("*.json"))
            if not dir_jsons:
                console.print(f"[yellow]Warning:[/yellow] No *.json files found in {p}")
            paths.extend(dir_jsons)
        else:
            paths.append(p)

    return paths