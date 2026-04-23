def extension_info(
    extension: str = typer.Argument(help="Extension ID or name"),
):
    """Show detailed information about an extension."""
    from .extensions import ExtensionCatalog, ExtensionManager, normalize_priority

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    catalog = ExtensionCatalog(project_root)
    manager = ExtensionManager(project_root)
    installed = manager.list_installed()

    # Try to resolve from installed extensions first (by ID or name)
    # Use allow_not_found=True since the extension may be catalog-only
    resolved_installed_id, resolved_installed_name = _resolve_installed_extension(
        extension, installed, "info", allow_not_found=True
    )

    # Try catalog lookup (with error handling)
    # If we resolved an installed extension by display name, use its ID for catalog lookup
    # to ensure we get the correct catalog entry (not a different extension with same name)
    lookup_key = resolved_installed_id if resolved_installed_id else extension
    ext_info, catalog_error = _resolve_catalog_extension(lookup_key, catalog, "info")

    # Case 1: Found in catalog - show full catalog info
    if ext_info:
        _print_extension_info(ext_info, manager)
        return

    # Case 2: Installed locally but catalog lookup failed or not in catalog
    if resolved_installed_id:
        # Get local manifest info
        ext_manifest = manager.get_extension(resolved_installed_id)
        metadata = manager.registry.get(resolved_installed_id)
        metadata_is_dict = isinstance(metadata, dict)
        if not metadata_is_dict:
            console.print(
                "[yellow]Warning:[/yellow] Extension metadata appears to be corrupted; "
                "some information may be unavailable."
            )
        version = metadata.get("version", "unknown") if metadata_is_dict else "unknown"

        console.print(f"\n[bold]{resolved_installed_name}[/bold] (v{version})")
        console.print(f"ID: {resolved_installed_id}")
        console.print()

        if ext_manifest:
            console.print(f"{ext_manifest.description}")
            console.print()
            # Author is optional in extension.yml, safely retrieve it
            author = ext_manifest.data.get("extension", {}).get("author")
            if author:
                console.print(f"[dim]Author:[/dim] {author}")
                console.print()

            if ext_manifest.commands:
                console.print("[bold]Commands:[/bold]")
                for cmd in ext_manifest.commands:
                    console.print(f"  • {cmd['name']}: {cmd.get('description', '')}")
                console.print()

        # Show catalog status
        if catalog_error:
            console.print(f"[yellow]Catalog unavailable:[/yellow] {catalog_error}")
            console.print("[dim]Note: Using locally installed extension; catalog info could not be verified.[/dim]")
        else:
            console.print("[yellow]Note:[/yellow] Not found in catalog (custom/local extension)")

        console.print()
        console.print("[green]✓ Installed[/green]")
        priority = normalize_priority(metadata.get("priority") if metadata_is_dict else None)
        console.print(f"[dim]Priority:[/dim] {priority}")
        console.print(f"\nTo remove: specify extension remove {resolved_installed_id}")
        return

    # Case 3: Not found anywhere
    if catalog_error:
        console.print(f"[red]Error:[/red] Could not query extension catalog: {catalog_error}")
        console.print("\nTry again when online, or use the extension ID directly.")
    else:
        console.print(f"[red]Error:[/red] Extension '{extension}' not found")
        console.print("\nTry: specify extension search")
    raise typer.Exit(1)