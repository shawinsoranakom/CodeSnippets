def extension_add(
    extension: str = typer.Argument(help="Extension name or path"),
    dev: bool = typer.Option(False, "--dev", help="Install from local directory"),
    from_url: Optional[str] = typer.Option(None, "--from", help="Install from custom URL"),
    priority: int = typer.Option(10, "--priority", help="Resolution priority (lower = higher precedence, default 10)"),
):
    """Install an extension."""
    from .extensions import ExtensionManager, ExtensionCatalog, ExtensionError, ValidationError, CompatibilityError, REINSTALL_COMMAND

    project_root = Path.cwd()

    # Check if we're in a spec-kit project
    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        console.print("Run this command from a spec-kit project root")
        raise typer.Exit(1)

    # Validate priority
    if priority < 1:
        console.print("[red]Error:[/red] Priority must be a positive integer (1 or higher)")
        raise typer.Exit(1)

    manager = ExtensionManager(project_root)
    speckit_version = get_speckit_version()

    try:
        with console.status(f"[cyan]Installing extension: {extension}[/cyan]"):
            if dev:
                # Install from local directory
                source_path = Path(extension).expanduser().resolve()
                if not source_path.exists():
                    console.print(f"[red]Error:[/red] Directory not found: {source_path}")
                    raise typer.Exit(1)

                if not (source_path / "extension.yml").exists():
                    console.print(f"[red]Error:[/red] No extension.yml found in {source_path}")
                    raise typer.Exit(1)

                manifest = manager.install_from_directory(source_path, speckit_version, priority=priority)

            elif from_url:
                # Install from URL (ZIP file)
                import urllib.request
                import urllib.error
                from urllib.parse import urlparse

                # Validate URL
                parsed = urlparse(from_url)
                is_localhost = parsed.hostname in ("localhost", "127.0.0.1", "::1")

                if parsed.scheme != "https" and not (parsed.scheme == "http" and is_localhost):
                    console.print("[red]Error:[/red] URL must use HTTPS for security.")
                    console.print("HTTP is only allowed for localhost URLs.")
                    raise typer.Exit(1)

                # Warn about untrusted sources
                console.print("[yellow]Warning:[/yellow] Installing from external URL.")
                console.print("Only install extensions from sources you trust.\n")
                console.print(f"Downloading from {from_url}...")

                # Download ZIP to temp location
                download_dir = project_root / ".specify" / "extensions" / ".cache" / "downloads"
                download_dir.mkdir(parents=True, exist_ok=True)
                zip_path = download_dir / f"{extension}-url-download.zip"

                try:
                    with urllib.request.urlopen(from_url, timeout=60) as response:
                        zip_data = response.read()
                    zip_path.write_bytes(zip_data)

                    # Install from downloaded ZIP
                    manifest = manager.install_from_zip(zip_path, speckit_version, priority=priority)
                except urllib.error.URLError as e:
                    console.print(f"[red]Error:[/red] Failed to download from {from_url}: {e}")
                    raise typer.Exit(1)
                finally:
                    # Clean up downloaded ZIP
                    if zip_path.exists():
                        zip_path.unlink()

            else:
                # Try bundled extensions first (shipped with spec-kit)
                bundled_path = _locate_bundled_extension(extension)
                if bundled_path is not None:
                    manifest = manager.install_from_directory(bundled_path, speckit_version, priority=priority)
                else:
                    # Install from catalog (also resolves display names to IDs)
                    catalog = ExtensionCatalog(project_root)

                    # Check if extension exists in catalog (supports both ID and display name)
                    ext_info, catalog_error = _resolve_catalog_extension(extension, catalog, "add")
                    if catalog_error:
                        console.print(f"[red]Error:[/red] Could not query extension catalog: {catalog_error}")
                        raise typer.Exit(1)
                    if not ext_info:
                        console.print(f"[red]Error:[/red] Extension '{extension}' not found in catalog")
                        console.print("\nSearch available extensions:")
                        console.print("  specify extension search")
                        raise typer.Exit(1)

                    # If catalog resolved a display name to an ID, check bundled again
                    resolved_id = ext_info['id']
                    if resolved_id != extension:
                        bundled_path = _locate_bundled_extension(resolved_id)
                        if bundled_path is not None:
                            manifest = manager.install_from_directory(bundled_path, speckit_version, priority=priority)

                    if bundled_path is None:
                        # Bundled extensions without a download URL must come from the local package
                        if ext_info.get("bundled") and not ext_info.get("download_url"):
                            console.print(
                                f"[red]Error:[/red] Extension '{ext_info['id']}' is bundled with spec-kit "
                                f"but could not be found in the installed package."
                            )
                            console.print(
                                "\nThis usually means the spec-kit installation is incomplete or corrupted."
                            )
                            console.print("Try reinstalling spec-kit:")
                            console.print(f"  {REINSTALL_COMMAND}")
                            raise typer.Exit(1)

                        # Enforce install_allowed policy
                        if not ext_info.get("_install_allowed", True):
                            catalog_name = ext_info.get("_catalog_name", "community")
                            console.print(
                                f"[red]Error:[/red] '{extension}' is available in the "
                                f"'{catalog_name}' catalog but installation is not allowed from that catalog."
                            )
                            console.print(
                                f"\nTo enable installation, add '{extension}' to an approved catalog "
                                f"(install_allowed: true) in .specify/extension-catalogs.yml."
                            )
                            raise typer.Exit(1)

                        # Download extension ZIP (use resolved ID, not original argument which may be display name)
                        extension_id = ext_info['id']
                        console.print(f"Downloading {ext_info['name']} v{ext_info.get('version', 'unknown')}...")
                        zip_path = catalog.download_extension(extension_id)

                        try:
                            # Install from downloaded ZIP
                            manifest = manager.install_from_zip(zip_path, speckit_version, priority=priority)
                        finally:
                            # Clean up downloaded ZIP
                            if zip_path.exists():
                                zip_path.unlink()

        console.print("\n[green]✓[/green] Extension installed successfully!")
        console.print(f"\n[bold]{manifest.name}[/bold] (v{manifest.version})")
        console.print(f"  {manifest.description}")

        for warning in manifest.warnings:
            console.print(f"\n[yellow]⚠  Compatibility warning:[/yellow] {warning}")

        console.print("\n[bold cyan]Provided commands:[/bold cyan]")
        for cmd in manifest.commands:
            console.print(f"  • {cmd['name']} - {cmd.get('description', '')}")

        # Report agent skills registration
        reg_meta = manager.registry.get(manifest.id)
        reg_skills = reg_meta.get("registered_skills", []) if reg_meta else []
        # Normalize to guard against corrupted registry entries
        if not isinstance(reg_skills, list):
            reg_skills = []
        if reg_skills:
            console.print(f"\n[green]✓[/green] {len(reg_skills)} agent skill(s) auto-registered")

        console.print("\n[yellow]⚠[/yellow]  Configuration may be required")
        console.print(f"   Check: .specify/extensions/{manifest.id}/")

    except ValidationError as e:
        console.print(f"\n[red]Validation Error:[/red] {e}")
        raise typer.Exit(1)
    except CompatibilityError as e:
        console.print(f"\n[red]Compatibility Error:[/red] {e}")
        raise typer.Exit(1)
    except ExtensionError as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)