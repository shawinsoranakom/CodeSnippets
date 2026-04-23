def integration_uninstall(
    key: str = typer.Argument(None, help="Integration key to uninstall (default: current integration)"),
    force: bool = typer.Option(False, "--force", help="Remove files even if modified"),
):
    """Uninstall an integration, safely preserving modified files."""
    from .integrations import get_integration
    from .integrations.manifest import IntegrationManifest

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    current = _read_integration_json(project_root)
    installed_key = current.get("integration")

    if key is None:
        if not installed_key:
            console.print("[yellow]No integration is currently installed.[/yellow]")
            raise typer.Exit(0)
        key = installed_key

    if installed_key and installed_key != key:
        console.print(f"[red]Error:[/red] Integration '{key}' is not the currently installed integration ('{installed_key}').")
        raise typer.Exit(1)

    integration = get_integration(key)

    manifest_path = project_root / ".specify" / "integrations" / f"{key}.manifest.json"
    if not manifest_path.exists():
        console.print(f"[yellow]No manifest found for integration '{key}'. Nothing to uninstall.[/yellow]")
        _remove_integration_json(project_root)
        # Clear integration-related keys from init-options.json
        opts = load_init_options(project_root)
        if opts.get("integration") == key or opts.get("ai") == key:
            opts.pop("integration", None)
            opts.pop("ai", None)
            opts.pop("ai_skills", None)
            opts.pop("context_file", None)
            save_init_options(project_root, opts)
        raise typer.Exit(0)

    try:
        manifest = IntegrationManifest.load(key, project_root)
    except (ValueError, FileNotFoundError) as exc:
        console.print(f"[red]Error:[/red] Integration manifest for '{key}' is unreadable.")
        console.print(f"Manifest: {manifest_path}")
        console.print(
            f"To recover, delete the unreadable manifest, run "
            f"[cyan]specify integration uninstall {key}[/cyan] to clear stale metadata, "
            f"then run [cyan]specify integration install {key}[/cyan] to regenerate."
        )
        console.print(f"[dim]Details:[/dim] {exc}")
        raise typer.Exit(1)

    removed, skipped = manifest.uninstall(project_root, force=force)

    # Remove managed context section from the agent context file
    if integration:
        integration.remove_context_section(project_root)

    _remove_integration_json(project_root)

    # Update init-options.json to clear the integration
    opts = load_init_options(project_root)
    if opts.get("integration") == key or opts.get("ai") == key:
        opts.pop("integration", None)
        opts.pop("ai", None)
        opts.pop("ai_skills", None)
        opts.pop("context_file", None)
        save_init_options(project_root, opts)

    name = (integration.config or {}).get("name", key) if integration else key
    console.print(f"\n[green]✓[/green] Integration '{name}' uninstalled")
    if removed:
        console.print(f"  Removed {len(removed)} file(s)")
    if skipped:
        console.print(f"\n[yellow]⚠[/yellow]  {len(skipped)} modified file(s) were preserved:")
        for path in skipped:
            rel = path.relative_to(project_root) if path.is_absolute() else path
            console.print(f"    {rel}")