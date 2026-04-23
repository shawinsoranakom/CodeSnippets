def integration_list(
    catalog: bool = typer.Option(False, "--catalog", help="Browse full catalog (built-in + community)"),
):
    """List available integrations and installed status."""
    from .integrations import INTEGRATION_REGISTRY

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    current = _read_integration_json(project_root)
    installed_key = current.get("integration")

    if catalog:
        from .integrations.catalog import IntegrationCatalog, IntegrationCatalogError

        ic = IntegrationCatalog(project_root)
        try:
            entries = ic.search()
        except IntegrationCatalogError as exc:
            console.print(f"[red]Error:[/red] {exc}")
            raise typer.Exit(1)

        if not entries:
            console.print("[yellow]No integrations found in catalog.[/yellow]")
            return

        table = Table(title="Integration Catalog")
        table.add_column("ID", style="cyan")
        table.add_column("Name")
        table.add_column("Version")
        table.add_column("Source")
        table.add_column("Status")

        for entry in sorted(entries, key=lambda e: e["id"]):
            eid = entry["id"]
            cat_name = entry.get("_catalog_name", "")
            install_allowed = entry.get("_install_allowed", True)
            if eid == installed_key:
                status = "[green]installed[/green]"
            elif eid in INTEGRATION_REGISTRY:
                status = "built-in"
            elif install_allowed is False:
                status = "discovery-only"
            else:
                status = ""
            table.add_row(
                eid,
                entry.get("name", eid),
                entry.get("version", ""),
                cat_name,
                status,
            )

        console.print(table)
        return

    table = Table(title="AI Agent Integrations")
    table.add_column("Key", style="cyan")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("CLI Required")

    for key in sorted(INTEGRATION_REGISTRY.keys()):
        integration = INTEGRATION_REGISTRY[key]
        cfg = integration.config or {}
        name = cfg.get("name", key)
        requires_cli = cfg.get("requires_cli", False)

        if key == installed_key:
            status = "[green]installed[/green]"
        else:
            status = ""

        cli_req = "yes" if requires_cli else "no (IDE)"
        table.add_row(key, name, status, cli_req)

    console.print(table)

    if installed_key:
        console.print(f"\n[dim]Current integration:[/dim] [cyan]{installed_key}[/cyan]")
    else:
        console.print("\n[yellow]No integration currently installed.[/yellow]")
        console.print("Install one with: [cyan]specify integration install <key>[/cyan]")