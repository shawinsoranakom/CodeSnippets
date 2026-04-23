def workflow_add(
    source: str = typer.Argument(..., help="Workflow ID, URL, or local path"),
):
    """Install a workflow from catalog, URL, or local path."""
    from .workflows.catalog import WorkflowCatalog, WorkflowRegistry, WorkflowCatalogError
    from .workflows.engine import WorkflowDefinition

    project_root = Path.cwd()
    specify_dir = project_root / ".specify"
    if not specify_dir.exists():
        console.print("[red]Error:[/red] Not a spec-kit project (no .specify/ directory)")
        raise typer.Exit(1)

    registry = WorkflowRegistry(project_root)
    workflows_dir = project_root / ".specify" / "workflows"

    def _validate_and_install_local(yaml_path: Path, source_label: str) -> None:
        """Validate and install a workflow from a local YAML file."""
        try:
            definition = WorkflowDefinition.from_yaml(yaml_path)
        except (ValueError, yaml.YAMLError) as exc:
            console.print(f"[red]Error:[/red] Invalid workflow YAML: {exc}")
            raise typer.Exit(1)
        if not definition.id or not definition.id.strip():
            console.print("[red]Error:[/red] Workflow definition has an empty or missing 'id'")
            raise typer.Exit(1)

        from .workflows.engine import validate_workflow
        errors = validate_workflow(definition)
        if errors:
            console.print("[red]Error:[/red] Workflow validation failed:")
            for err in errors:
                console.print(f"  \u2022 {err}")
            raise typer.Exit(1)

        dest_dir = workflows_dir / definition.id
        dest_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(yaml_path, dest_dir / "workflow.yml")
        registry.add(definition.id, {
            "name": definition.name,
            "version": definition.version,
            "description": definition.description,
            "source": source_label,
        })
        console.print(f"[green]✓[/green] Workflow '{definition.name}' ({definition.id}) installed")

    # Try as URL (http/https)
    if source.startswith("http://") or source.startswith("https://"):
        from ipaddress import ip_address
        from urllib.parse import urlparse
        from urllib.request import urlopen  # noqa: S310

        parsed_src = urlparse(source)
        src_host = parsed_src.hostname or ""
        src_loopback = src_host == "localhost"
        if not src_loopback:
            try:
                src_loopback = ip_address(src_host).is_loopback
            except ValueError:
                # Host is not an IP literal (e.g., a DNS name); keep default non-loopback.
                pass
        if parsed_src.scheme != "https" and not (parsed_src.scheme == "http" and src_loopback):
            console.print("[red]Error:[/red] Only HTTPS URLs are allowed, except HTTP for localhost.")
            raise typer.Exit(1)

        import tempfile
        try:
            with urlopen(source, timeout=30) as resp:  # noqa: S310
                final_url = resp.geturl()
                final_parsed = urlparse(final_url)
                final_host = final_parsed.hostname or ""
                final_lb = final_host == "localhost"
                if not final_lb:
                    try:
                        final_lb = ip_address(final_host).is_loopback
                    except ValueError:
                        # Redirect host is not an IP literal; keep loopback as determined above.
                        pass
                if final_parsed.scheme != "https" and not (final_parsed.scheme == "http" and final_lb):
                    console.print(f"[red]Error:[/red] URL redirected to non-HTTPS: {final_url}")
                    raise typer.Exit(1)
                with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as tmp:
                    tmp.write(resp.read())
                    tmp_path = Path(tmp.name)
        except typer.Exit:
            raise
        except Exception as exc:
            console.print(f"[red]Error:[/red] Failed to download workflow: {exc}")
            raise typer.Exit(1)
        try:
            _validate_and_install_local(tmp_path, source)
        finally:
            tmp_path.unlink(missing_ok=True)
        return

    # Try as a local file/directory
    source_path = Path(source)
    if source_path.exists():
        if source_path.is_file() and source_path.suffix in (".yml", ".yaml"):
            _validate_and_install_local(source_path, str(source_path))
            return
        elif source_path.is_dir():
            wf_file = source_path / "workflow.yml"
            if not wf_file.exists():
                console.print(f"[red]Error:[/red] No workflow.yml found in {source}")
                raise typer.Exit(1)
            _validate_and_install_local(wf_file, str(source_path))
            return

    # Try from catalog
    catalog = WorkflowCatalog(project_root)
    try:
        info = catalog.get_workflow_info(source)
    except WorkflowCatalogError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1)

    if not info:
        console.print(f"[red]Error:[/red] Workflow '{source}' not found in catalog")
        raise typer.Exit(1)

    if not info.get("_install_allowed", True):
        console.print(f"[yellow]Warning:[/yellow] Workflow '{source}' is from a discovery-only catalog")
        console.print("Direct installation is not enabled for this catalog source.")
        raise typer.Exit(1)

    workflow_url = info.get("url")
    if not workflow_url:
        console.print(f"[red]Error:[/red] Workflow '{source}' does not have an install URL in the catalog")
        raise typer.Exit(1)

    # Validate URL scheme (HTTPS required, HTTP allowed for localhost only)
    from ipaddress import ip_address
    from urllib.parse import urlparse

    parsed_url = urlparse(workflow_url)
    url_host = parsed_url.hostname or ""
    is_loopback = False
    if url_host == "localhost":
        is_loopback = True
    else:
        try:
            is_loopback = ip_address(url_host).is_loopback
        except ValueError:
            # Host is not an IP literal (e.g., a regular hostname); treat as non-loopback.
            pass
    if parsed_url.scheme != "https" and not (parsed_url.scheme == "http" and is_loopback):
        console.print(
            f"[red]Error:[/red] Workflow '{source}' has an invalid install URL. "
            "Only HTTPS URLs are allowed, except HTTP for localhost/loopback."
        )
        raise typer.Exit(1)

    workflow_dir = workflows_dir / source
    # Validate that source is a safe directory name (no path traversal)
    try:
        workflow_dir.resolve().relative_to(workflows_dir.resolve())
    except ValueError:
        console.print(f"[red]Error:[/red] Invalid workflow ID: {source!r}")
        raise typer.Exit(1)
    workflow_file = workflow_dir / "workflow.yml"

    try:
        from urllib.request import urlopen  # noqa: S310 — URL comes from catalog

        workflow_dir.mkdir(parents=True, exist_ok=True)
        with urlopen(workflow_url, timeout=30) as response:  # noqa: S310
            # Validate final URL after redirects
            final_url = response.geturl()
            final_parsed = urlparse(final_url)
            final_host = final_parsed.hostname or ""
            final_loopback = final_host == "localhost"
            if not final_loopback:
                try:
                    final_loopback = ip_address(final_host).is_loopback
                except ValueError:
                    # Host is not an IP literal (e.g., a regular hostname); treat as non-loopback.
                    pass
            if final_parsed.scheme != "https" and not (final_parsed.scheme == "http" and final_loopback):
                if workflow_dir.exists():
                    import shutil
                    shutil.rmtree(workflow_dir, ignore_errors=True)
                console.print(
                    f"[red]Error:[/red] Workflow '{source}' redirected to non-HTTPS URL: {final_url}"
                )
                raise typer.Exit(1)
            workflow_file.write_bytes(response.read())
    except Exception as exc:
        if workflow_dir.exists():
            import shutil
            shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print(f"[red]Error:[/red] Failed to install workflow '{source}' from catalog: {exc}")
        raise typer.Exit(1)

    # Validate the downloaded workflow before registering
    try:
        definition = WorkflowDefinition.from_yaml(workflow_file)
    except (ValueError, yaml.YAMLError) as exc:
        import shutil
        shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print(f"[red]Error:[/red] Downloaded workflow is invalid: {exc}")
        raise typer.Exit(1)

    from .workflows.engine import validate_workflow
    errors = validate_workflow(definition)
    if errors:
        import shutil
        shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print("[red]Error:[/red] Downloaded workflow validation failed:")
        for err in errors:
            console.print(f"  \u2022 {err}")
        raise typer.Exit(1)

    # Enforce that the workflow's internal ID matches the catalog key
    if definition.id and definition.id != source:
        import shutil
        shutil.rmtree(workflow_dir, ignore_errors=True)
        console.print(
            f"[red]Error:[/red] Workflow ID in YAML ({definition.id!r}) "
            f"does not match catalog key ({source!r}). "
            f"The catalog entry may be misconfigured."
        )
        raise typer.Exit(1)

    registry.add(source, {
        "name": definition.name or info.get("name", source),
        "version": definition.version or info.get("version", "0.0.0"),
        "description": definition.description or info.get("description", ""),
        "source": "catalog",
        "catalog_name": info.get("_catalog_name", ""),
        "url": workflow_url,
    })
    console.print(f"[green]✓[/green] Workflow '{info.get('name', source)}' installed from catalog")