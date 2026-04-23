def workflow_info(
    workflow_id: str = typer.Argument(..., help="Workflow ID"),
):
    """Show workflow details and step graph."""
    from .workflows.catalog import WorkflowCatalog, WorkflowRegistry, WorkflowCatalogError
    from .workflows.engine import WorkflowEngine

    project_root = Path.cwd()
    if not (project_root / ".specify").exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        raise typer.Exit(1)

    # Check installed first
    registry = WorkflowRegistry(project_root)
    installed = registry.get(workflow_id)

    engine = WorkflowEngine(project_root)

    definition = None
    try:
        definition = engine.load_workflow(workflow_id)
    except FileNotFoundError:
        # Local workflow definition not found on disk; fall back to
        # catalog/registry lookup below.
        pass

    if definition:
        console.print(f"\n[bold cyan]{definition.name}[/bold cyan] ({definition.id})")
        console.print(f"  Version:     {definition.version}")
        if definition.author:
            console.print(f"  Author:      {definition.author}")
        if definition.description:
            console.print(f"  Description: {definition.description}")
        if definition.default_integration:
            console.print(f"  Integration: {definition.default_integration}")
        if installed:
            console.print("  [green]Installed[/green]")

        if definition.inputs:
            console.print("\n  [bold]Inputs:[/bold]")
            for name, inp in definition.inputs.items():
                if isinstance(inp, dict):
                    req = "required" if inp.get("required") else "optional"
                    console.print(f"    {name} ({inp.get('type', 'string')}) — {req}")

        if definition.steps:
            console.print(f"\n  [bold]Steps ({len(definition.steps)}):[/bold]")
            for step in definition.steps:
                stype = step.get("type", "command")
                console.print(f"    → {step.get('id', '?')} [{stype}]")
        return

    # Try catalog
    catalog = WorkflowCatalog(project_root)
    try:
        info = catalog.get_workflow_info(workflow_id)
    except WorkflowCatalogError:
        info = None

    if info:
        console.print(f"\n[bold cyan]{info.get('name', workflow_id)}[/bold cyan] ({workflow_id})")
        console.print(f"  Version:     {info.get('version', '?')}")
        if info.get("description"):
            console.print(f"  Description: {info['description']}")
        if info.get("tags"):
            console.print(f"  Tags:        {', '.join(info['tags'])}")
        console.print("  [yellow]Not installed[/yellow]")
    else:
        console.print(f"[red]Error:[/red] Workflow '{workflow_id}' not found")
        raise typer.Exit(1)