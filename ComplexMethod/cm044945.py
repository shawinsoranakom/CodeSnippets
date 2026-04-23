def integration_install(
    key: str = typer.Argument(help="Integration key to install (e.g. claude, copilot)"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh or ps (default: from init-options.json or platform default)"),
    integration_options: str | None = typer.Option(None, "--integration-options", help='Options for the integration (e.g. --integration-options="--commands-dir .myagent/cmds")'),
):
    """Install an integration into an existing project."""
    from .integrations import INTEGRATION_REGISTRY, get_integration
    from .integrations.manifest import IntegrationManifest

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    integration = get_integration(key)
    if integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{key}'")
        available = ", ".join(sorted(INTEGRATION_REGISTRY.keys()))
        console.print(f"Available integrations: {available}")
        raise typer.Exit(1)

    current = _read_integration_json(project_root)
    installed_key = current.get("integration")

    if installed_key and installed_key == key:
        console.print(f"[yellow]Integration '{key}' is already installed.[/yellow]")
        console.print("Run [cyan]specify integration uninstall[/cyan] first, then reinstall.")
        raise typer.Exit(0)

    if installed_key:
        console.print(f"[red]Error:[/red] Integration '{installed_key}' is already installed.")
        console.print(f"Run [cyan]specify integration uninstall[/cyan] first, or use [cyan]specify integration switch {key}[/cyan].")
        raise typer.Exit(1)

    selected_script = _resolve_script_type(project_root, script)

    # Ensure shared infrastructure is present (safe to run unconditionally;
    # _install_shared_infra merges missing files without overwriting).
    _install_shared_infra(project_root, selected_script)
    if os.name != "nt":
        ensure_executable_scripts(project_root)

    manifest = IntegrationManifest(
        integration.key, project_root, version=get_speckit_version()
    )

    # Build parsed options from --integration-options
    parsed_options: dict[str, Any] | None = None
    if integration_options:
        parsed_options = _parse_integration_options(integration, integration_options)

    try:
        integration.setup(
            project_root, manifest,
            parsed_options=parsed_options,
            script_type=selected_script,
            raw_options=integration_options,
        )
        manifest.save()
        _write_integration_json(project_root, integration.key)
        _update_init_options_for_integration(project_root, integration, script_type=selected_script)

    except Exception as e:
        # Attempt rollback of any files written by setup
        try:
            integration.teardown(project_root, manifest, force=True)
        except Exception as rollback_err:
            # Suppress so the original setup error remains the primary failure
            console.print(f"[yellow]Warning:[/yellow] Failed to roll back integration changes: {rollback_err}")
        _remove_integration_json(project_root)
        console.print(f"[red]Error:[/red] Failed to install integration: {e}")
        raise typer.Exit(1)

    name = (integration.config or {}).get("name", key)
    console.print(f"\n[green]✓[/green] Integration '{name}' installed successfully")