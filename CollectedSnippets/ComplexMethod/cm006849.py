def pull_command(
    *,
    env: str | None,
    output_dir: str | None,
    flow_id: str | None,
    project: str | None,
    project_id: str | None,
    environments_file: str | None,
    target: str | None = None,
    api_key: str | None = None,
    strip_secrets: bool,
    indent: int,
) -> None:
    sdk = load_sdk("pull")

    from lfx.config import ConfigError, resolve_environment

    try:
        env_cfg = resolve_environment(
            env,
            target=target,
            api_key=api_key,
            environments_file=environments_file,
        )
    except ConfigError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(1) from exc

    client = sdk.Client(base_url=env_cfg.url, api_key=env_cfg.api_key)

    dest_dir = Path(output_dir) if output_dir else Path("flows")
    dest_dir.mkdir(parents=True, exist_ok=True)

    results: list[PullResult] = []

    # ---- Single flow by ID -----------------------------------------------
    if flow_id:
        try:
            flow_obj = client.get_flow(UUID(flow_id))
        except Exception as exc:
            console.print(f"[red]Error:[/red] Could not fetch flow {flow_id}: {exc}")
            raise typer.Exit(1) from exc

        result = _write_flow(flow_obj, sdk=sdk, dest_dir=dest_dir, strip_secrets=strip_secrets, indent=indent)
        results.append(result)
        if result.ok:
            console.print(f"[green]Pulled[/green] {result.flow_name!r} → {result.path}")
        else:
            console.print(f"[red]Failed[/red] {result.flow_name!r}: {result.error}")

    # ---- All flows in a named project ------------------------------------
    elif project or project_id:
        if project_id:
            try:
                proj = client.get_project(UUID(project_id))
            except Exception as exc:
                console.print(f"[red]Error:[/red] Could not fetch project {project_id}: {exc}")
                raise typer.Exit(1) from exc
        else:
            projects = client.list_projects()
            matched = [p for p in projects if p.name == project]
            if not matched:
                names = ", ".join(repr(p.name) for p in projects) or "(none)"
                console.print(f"[red]Error:[/red] Project {project!r} not found. Available: {names}")
                raise typer.Exit(1)
            try:
                proj = client.get_project(matched[0].id)
            except Exception as exc:
                console.print(f"[red]Error:[/red] Could not fetch project {project!r}: {exc}")
                raise typer.Exit(1) from exc

        console.print(f"[dim]Pulling from project[/dim] {proj.name!r} (id={proj.id})")

        for flow_obj in proj.flows:
            result = _write_flow(flow_obj, sdk=sdk, dest_dir=dest_dir, strip_secrets=strip_secrets, indent=indent)
            results.append(result)
            if result.status == "unchanged":
                console.print(f"[dim]Unchanged[/dim] {result.flow_name!r}")
            elif result.ok:
                console.print(f"[green]Pulled[/green] {result.flow_name!r} → {result.path}")
            else:
                console.print(f"[red]Failed[/red] {result.flow_name!r}: {result.error}")

    # ---- All flows in the environment ------------------------------------
    else:
        console.print(f"[dim]Pulling all flows from[/dim] {env_cfg.url}")
        try:
            flows = client.list_flows(get_all=True, remove_example_flows=True)
        except Exception as exc:
            console.print(f"[red]Error:[/red] Could not list flows: {exc}")
            raise typer.Exit(1) from exc

        if not flows:
            console.print("[yellow]Warning:[/yellow] No flows found on the remote instance.")
            return

        for flow_obj in flows:
            result = _write_flow(flow_obj, sdk=sdk, dest_dir=dest_dir, strip_secrets=strip_secrets, indent=indent)
            results.append(result)
            if result.status == "unchanged":
                console.print(f"[dim]Unchanged[/dim] {result.flow_name!r}")
            elif result.ok:
                console.print(f"[green]Pulled[/green] {result.flow_name!r} → {result.path}")
            else:
                console.print(f"[red]Failed[/red] {result.flow_name!r}: {result.error}")

    _render_results(results)

    if any(not r.ok for r in results):
        raise typer.Exit(1)