def preset_info(
    preset_id: str = typer.Argument(..., help="Preset ID to get info about"),
):
    """Show detailed information about a preset."""
    from .extensions import normalize_priority
    from .presets import PresetCatalog, PresetManager, PresetError

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    # Check if installed locally first
    manager = PresetManager(project_root)
    local_pack = manager.get_pack(preset_id)

    if local_pack:
        console.print(f"\n[bold cyan]Preset: {local_pack.name}[/bold cyan]\n")
        console.print(f"  ID:          {local_pack.id}")
        console.print(f"  Version:     {local_pack.version}")
        console.print(f"  Description: {local_pack.description}")
        if local_pack.author:
            console.print(f"  Author:      {local_pack.author}")
        if local_pack.tags:
            console.print(f"  Tags:        {', '.join(local_pack.tags)}")
        console.print(f"  Templates:   {len(local_pack.templates)}")
        for tmpl in local_pack.templates:
            console.print(f"    - {tmpl['name']} ({tmpl['type']}): {tmpl.get('description', '')}")
        repo = local_pack.data.get("preset", {}).get("repository")
        if repo:
            console.print(f"  Repository:  {repo}")
        license_val = local_pack.data.get("preset", {}).get("license")
        if license_val:
            console.print(f"  License:     {license_val}")
        console.print("\n  [green]Status: installed[/green]")
        # Get priority from registry
        pack_metadata = manager.registry.get(preset_id)
        priority = normalize_priority(pack_metadata.get("priority") if isinstance(pack_metadata, dict) else None)
        console.print(f"  [dim]Priority:[/dim] {priority}")
        console.print()
        return

    # Fall back to catalog
    catalog = PresetCatalog(project_root)
    try:
        pack_info = catalog.get_pack_info(preset_id)
    except PresetError:
        pack_info = None

    if not pack_info:
        console.print(f"[red]Error:[/red] Preset '{preset_id}' not found (not installed and not in catalog)")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Preset: {pack_info.get('name', preset_id)}[/bold cyan]\n")
    console.print(f"  ID:          {pack_info['id']}")
    console.print(f"  Version:     {pack_info.get('version', '?')}")
    console.print(f"  Description: {pack_info.get('description', '')}")
    if pack_info.get("author"):
        console.print(f"  Author:      {pack_info['author']}")
    if pack_info.get("tags"):
        console.print(f"  Tags:        {', '.join(pack_info['tags'])}")
    if pack_info.get("repository"):
        console.print(f"  Repository:  {pack_info['repository']}")
    if pack_info.get("license"):
        console.print(f"  License:     {pack_info['license']}")
    console.print("\n  [yellow]Status: not installed[/yellow]")
    console.print(f"  Install with: [cyan]specify preset add {preset_id}[/cyan]")
    console.print()