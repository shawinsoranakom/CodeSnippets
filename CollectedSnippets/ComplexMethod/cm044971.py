def workflow_status(
    run_id: str | None = typer.Argument(None, help="Run ID to inspect (shows all if omitted)"),
):
    """Show workflow run status."""
    from .workflows.engine import WorkflowEngine

    project_root = Path.cwd()
    if not (project_root / ".specify").exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        raise typer.Exit(1)
    engine = WorkflowEngine(project_root)

    if run_id:
        try:
            from .workflows.engine import RunState
            state = RunState.load(run_id, project_root)
        except FileNotFoundError:
            console.print(f"[red]Error:[/red] Run not found: {run_id}")
            raise typer.Exit(1)

        status_colors = {
            "completed": "green",
            "paused": "yellow",
            "failed": "red",
            "aborted": "red",
            "running": "blue",
            "created": "dim",
        }
        color = status_colors.get(state.status.value, "white")

        console.print(f"\n[bold cyan]Workflow Run: {state.run_id}[/bold cyan]")
        console.print(f"  Workflow: {state.workflow_id}")
        console.print(f"  Status:   [{color}]{state.status.value}[/{color}]")
        console.print(f"  Created:  {state.created_at}")
        console.print(f"  Updated:  {state.updated_at}")

        if state.current_step_id:
            console.print(f"  Current:  {state.current_step_id}")

        if state.step_results:
            console.print(f"\n  [bold]Steps ({len(state.step_results)}):[/bold]")
            for step_id, step_data in state.step_results.items():
                s = step_data.get("status", "unknown")
                sc = {"completed": "green", "failed": "red", "paused": "yellow"}.get(s, "white")
                console.print(f"    [{sc}]●[/{sc}] {step_id}: {s}")
    else:
        runs = engine.list_runs()
        if not runs:
            console.print("[yellow]No workflow runs found.[/yellow]")
            return

        console.print("\n[bold cyan]Workflow Runs:[/bold cyan]\n")
        for run_data in runs:
            s = run_data.get("status", "unknown")
            sc = {"completed": "green", "failed": "red", "paused": "yellow", "running": "blue"}.get(s, "white")
            console.print(
                f"  [{sc}]●[/{sc}] {run_data['run_id']}  "
                f"{run_data.get('workflow_id', '?')}  "
                f"[{sc}]{s}[/{sc}]  "
                f"[dim]{run_data.get('updated_at', '?')}[/dim]"
            )