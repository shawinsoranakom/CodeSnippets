def _print_extension_info(ext_info: dict, manager):
    """Print formatted extension info from catalog data."""
    from .extensions import normalize_priority

    # Header
    verified_badge = " [green]✓ Verified[/green]" if ext_info.get("verified") else ""
    console.print(f"\n[bold]{ext_info['name']}[/bold] (v{ext_info['version']}){verified_badge}")
    console.print(f"ID: {ext_info['id']}")
    console.print()

    # Description
    console.print(f"{ext_info['description']}")
    console.print()

    # Author and License
    console.print(f"[dim]Author:[/dim] {ext_info.get('author', 'Unknown')}")
    console.print(f"[dim]License:[/dim] {ext_info.get('license', 'Unknown')}")

    # Source catalog
    if ext_info.get("_catalog_name"):
        install_allowed = ext_info.get("_install_allowed", True)
        install_note = "" if install_allowed else " [yellow](discovery only)[/yellow]"
        console.print(f"[dim]Source catalog:[/dim] {ext_info['_catalog_name']}{install_note}")
    console.print()

    # Requirements
    if ext_info.get('requires'):
        console.print("[bold]Requirements:[/bold]")
        reqs = ext_info['requires']
        if reqs.get('speckit_version'):
            console.print(f"  • Spec Kit: {reqs['speckit_version']}")
        if reqs.get('tools'):
            for tool in reqs['tools']:
                tool_name = tool['name']
                tool_version = tool.get('version', 'any')
                required = " (required)" if tool.get('required') else " (optional)"
                console.print(f"  • {tool_name}: {tool_version}{required}")
        console.print()

    # Provides
    if ext_info.get('provides'):
        console.print("[bold]Provides:[/bold]")
        provides = ext_info['provides']
        if provides.get('commands'):
            console.print(f"  • Commands: {provides['commands']}")
        if provides.get('hooks'):
            console.print(f"  • Hooks: {provides['hooks']}")
        console.print()

    # Tags
    if ext_info.get('tags'):
        tags_str = ", ".join(ext_info['tags'])
        console.print(f"[bold]Tags:[/bold] {tags_str}")
        console.print()

    # Statistics
    stats = []
    if ext_info.get('downloads') is not None:
        stats.append(f"Downloads: {ext_info['downloads']:,}")
    if ext_info.get('stars') is not None:
        stats.append(f"Stars: {ext_info['stars']}")
    if stats:
        console.print(f"[bold]Statistics:[/bold] {' | '.join(stats)}")
        console.print()

    # Links
    console.print("[bold]Links:[/bold]")
    if ext_info.get('repository'):
        console.print(f"  • Repository: {ext_info['repository']}")
    if ext_info.get('homepage'):
        console.print(f"  • Homepage: {ext_info['homepage']}")
    if ext_info.get('documentation'):
        console.print(f"  • Documentation: {ext_info['documentation']}")
    if ext_info.get('changelog'):
        console.print(f"  • Changelog: {ext_info['changelog']}")
    console.print()

    # Installation status and command
    is_installed = manager.registry.is_installed(ext_info['id'])
    install_allowed = ext_info.get("_install_allowed", True)
    if is_installed:
        console.print("[green]✓ Installed[/green]")
        metadata = manager.registry.get(ext_info['id'])
        priority = normalize_priority(metadata.get("priority") if isinstance(metadata, dict) else None)
        console.print(f"[dim]Priority:[/dim] {priority}")
        console.print(f"\nTo remove: specify extension remove {ext_info['id']}")
    elif install_allowed:
        console.print("[yellow]Not installed[/yellow]")
        console.print(f"\n[cyan]Install:[/cyan] specify extension add {ext_info['id']}")
    else:
        catalog_name = ext_info.get("_catalog_name", "community")
        console.print("[yellow]Not installed[/yellow]")
        console.print(
            f"\n[yellow]⚠[/yellow]  '{ext_info['id']}' is available in the '{catalog_name}' catalog "
            f"but not in your approved catalog. Add it to .specify/extension-catalogs.yml "
            f"with install_allowed: true to enable installation."
        )