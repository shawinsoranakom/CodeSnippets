def integration_switch(
    target: str = typer.Argument(help="Integration key to switch to"),
    script: str | None = typer.Option(None, "--script", help="Script type: sh or ps (default: from init-options.json or platform default)"),
    force: bool = typer.Option(False, "--force", help="Force removal of modified files during uninstall"),
    integration_options: str | None = typer.Option(None, "--integration-options", help='Options for the target integration'),
):
    """Switch from the current integration to a different one."""
    from .integrations import INTEGRATION_REGISTRY, get_integration
    from .integrations.manifest import IntegrationManifest

    project_root = Path.cwd()

    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    target_integration = get_integration(target)
    if target_integration is None:
        console.print(f"[red]Error:[/red] Unknown integration '{target}'")
        available = ", ".join(sorted(INTEGRATION_REGISTRY.keys()))
        console.print(f"Available integrations: {available}")
        raise typer.Exit(1)

    current = _read_integration_json(project_root)
    installed_key = current.get("integration")

    if installed_key == target:
        console.print(f"[yellow]Integration '{target}' is already installed. Nothing to switch.[/yellow]")
        raise typer.Exit(0)

    selected_script = _resolve_script_type(project_root, script)

    # Phase 1: Uninstall current integration (if any)
    if installed_key:
        current_integration = get_integration(installed_key)
        manifest_path = project_root / ".specify" / "integrations" / f"{installed_key}.manifest.json"

        if current_integration and manifest_path.exists():
            console.print(f"Uninstalling current integration: [cyan]{installed_key}[/cyan]")
            try:
                old_manifest = IntegrationManifest.load(installed_key, project_root)
            except (ValueError, FileNotFoundError) as exc:
                console.print(f"[red]Error:[/red] Could not read integration manifest for '{installed_key}': {manifest_path}")
                console.print(f"[dim]{exc}[/dim]")
                console.print(
                    f"To recover, delete the unreadable manifest at {manifest_path}, "
                    f"run [cyan]specify integration uninstall {installed_key}[/cyan], then retry."
                )
                raise typer.Exit(1)
            removed, skipped = old_manifest.uninstall(project_root, force=force)
            current_integration.remove_context_section(project_root)
            if removed:
                console.print(f"  Removed {len(removed)} file(s)")
            if skipped:
                console.print(f"  [yellow]⚠[/yellow]  {len(skipped)} modified file(s) preserved")
        elif not current_integration and manifest_path.exists():
            # Integration removed from registry but manifest exists — use manifest-only uninstall
            console.print(f"Uninstalling unknown integration '{installed_key}' via manifest")
            try:
                old_manifest = IntegrationManifest.load(installed_key, project_root)
                removed, skipped = old_manifest.uninstall(project_root, force=force)
                if removed:
                    console.print(f"  Removed {len(removed)} file(s)")
                if skipped:
                    console.print(f"  [yellow]⚠[/yellow]  {len(skipped)} modified file(s) preserved")
            except (ValueError, FileNotFoundError) as exc:
                console.print(f"[yellow]Warning:[/yellow] Could not read manifest for '{installed_key}': {exc}")
        else:
            console.print(f"[red]Error:[/red] Integration '{installed_key}' is installed but has no manifest.")
            console.print(
                f"Run [cyan]specify integration uninstall {installed_key}[/cyan] to clear metadata, "
                f"then retry [cyan]specify integration switch {target}[/cyan]."
            )
            raise typer.Exit(1)

        # Clear metadata so a failed Phase 2 doesn't leave stale references
        _remove_integration_json(project_root)
        opts = load_init_options(project_root)
        opts.pop("integration", None)
        opts.pop("ai", None)
        opts.pop("ai_skills", None)
        opts.pop("context_file", None)
        save_init_options(project_root, opts)

    # Ensure shared infrastructure is present (safe to run unconditionally;
    # _install_shared_infra merges missing files without overwriting).
    _install_shared_infra(project_root, selected_script)
    if os.name != "nt":
        ensure_executable_scripts(project_root)

    # Phase 2: Install target integration
    console.print(f"Installing integration: [cyan]{target}[/cyan]")
    manifest = IntegrationManifest(
        target_integration.key, project_root, version=get_speckit_version()
    )

    parsed_options: dict[str, Any] | None = None
    if integration_options:
        parsed_options = _parse_integration_options(target_integration, integration_options)

    try:
        target_integration.setup(
            project_root, manifest,
            parsed_options=parsed_options,
            script_type=selected_script,
            raw_options=integration_options,
        )
        manifest.save()
        _write_integration_json(project_root, target_integration.key)
        _update_init_options_for_integration(project_root, target_integration, script_type=selected_script)

    except Exception as e:
        # Attempt rollback of any files written by setup
        try:
            target_integration.teardown(project_root, manifest, force=True)
        except Exception as rollback_err:
            # Suppress so the original setup error remains the primary failure
            console.print(f"[yellow]Warning:[/yellow] Failed to roll back integration '{target}': {rollback_err}")
        _remove_integration_json(project_root)
        console.print(f"[red]Error:[/red] Failed to install integration '{target}': {e}")
        raise typer.Exit(1)

    name = (target_integration.config or {}).get("name", target)
    console.print(f"\n[green]✓[/green] Switched to integration '{name}'")