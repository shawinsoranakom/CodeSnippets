def push_command(
    flow_paths: list[str],
    *,
    env: str | None,
    dir_path: str | None,
    project: str | None,
    project_id: str | None,
    environments_file: str | None,
    target: str | None = None,
    api_key: str | None = None,
    dry_run: bool,
    normalize: bool,
    strip_secrets: bool,
) -> None:
    sdk = load_sdk("push")

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

    paths = _collect_flow_files(flow_paths, dir_path)
    if not paths:
        console.print(
            "[red]Error:[/red] No *.json flow files found. "
            "Run [bold]lfx pull[/bold] first, or pass explicit file paths."
        )
        raise typer.Exit(1)

    # Resolve target project folder_id
    target_folder_id: UUID | None = None
    if project_id:
        target_folder_id = UUID(project_id)
    elif project:
        target_folder_id = _find_or_create_project(client, sdk, project, dry_run=dry_run)

    results: list[PushResult] = []

    for path in paths:
        raw_flow = _load_flow_file(path)

        if normalize:
            raw_flow = sdk.normalize_flow(
                raw_flow,
                strip_volatile=True,
                strip_secrets=strip_secrets,
                sort_keys=True,
            )

        flow_id = _extract_flow_id(raw_flow, path)
        flow_name = raw_flow.get("name", path.stem)
        flow_create = _flow_to_create(sdk, raw_flow, target_folder_id)
        # Capture normalized content now so _upsert_single can compare against remote.
        local_file_content = sdk.flow_to_json(raw_flow) if normalize else None

        result = _upsert_single(
            client,
            sdk,
            path,
            flow_id,
            flow_create,
            dry_run=dry_run,
            flow_name=flow_name,
            base_url=env_cfg.url,
            local_file_content=local_file_content,
            strip_secrets=strip_secrets,
        )
        results.append(result)

        if dry_run:
            console.print(f"[yellow]DRY-RUN[/yellow] Would push {flow_name!r} ({flow_id})")
        elif result.status == "unchanged":
            console.print(f"[dim]Unchanged[/dim] {flow_name!r}")
        elif result.status == "created":
            url_hint = f"  [dim]{result.flow_url}[/dim]" if result.flow_url else ""
            console.print(f"[green]Created[/green]  {flow_name!r} ({flow_id}){url_hint}")
        elif result.status == "updated":
            url_hint = f"  [dim]{result.flow_url}[/dim]" if result.flow_url else ""
            console.print(f"[cyan]Updated[/cyan]  {flow_name!r} ({flow_id}){url_hint}")
        else:
            console.print(f"[red]Failed[/red]   {flow_name!r} ({flow_id}): {result.error}")

    _render_results(results, dry_run=dry_run)

    if any(not r.ok for r in results):
        raise typer.Exit(1)