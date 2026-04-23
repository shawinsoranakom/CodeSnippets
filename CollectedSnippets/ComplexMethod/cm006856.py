def status_command(
    dir_path: str | None,
    flow_paths: list[str],
    env: str | None,
    environments_file: str | None,
    *,
    target: str | None = None,
    api_key: str | None = None,
    show_remote_only: bool,
) -> None:
    """Compare local flow files against the remote instance and render a status table."""
    normalize_flow, flow_to_json, client_cls, not_found_error = _load_sdk()

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

    try:
        client = client_cls(base_url=env_cfg.url, api_key=env_cfg.api_key)
    except Exception as exc:
        console.print(f"[red]Error:[/red] Could not create client for {env_cfg.url!r}: {exc}")
        raise typer.Exit(1) from exc

    try:
        env_label = env_cfg.name
        local_files = _collect_files(dir_path, flow_paths)

        if not local_files and not show_remote_only:
            console.print("[yellow]No flow files found.[/yellow] Use [bold]--dir[/bold] to specify a directory.")
            raise typer.Exit(0)

        statuses: list[FlowStatus] = []
        seen_ids: set[UUID] = set()

        # ------------------------------------------------------------------ #
        # Check each local file                                               #
        # ------------------------------------------------------------------ #
        for path in local_files:
            if not path.exists():
                statuses.append(FlowStatus(name=path.name, status=_STATUS_ERROR, path=path, detail="file not found"))
                continue

            try:
                raw: dict = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                statuses.append(FlowStatus(name=path.name, status=_STATUS_ERROR, path=path, detail=str(exc)))
                continue

            name: str = raw.get("name", path.stem)
            raw_id = raw.get("id")

            if not raw_id:
                statuses.append(
                    FlowStatus(
                        name=name,
                        status=_STATUS_NO_ID,
                        path=path,
                        detail="run lfx export --env <env> first to assign a stable id",
                    )
                )
                continue

            try:
                flow_id = UUID(str(raw_id))
            except ValueError:
                statuses.append(
                    FlowStatus(name=name, status=_STATUS_ERROR, path=path, detail=f"invalid id: {raw_id!r}")
                )
                continue

            seen_ids.add(flow_id)

            try:
                remote_flow = client.get_flow(flow_id)
            except not_found_error:
                statuses.append(FlowStatus(name=name, status=_STATUS_NEW, path=path, flow_id=flow_id))
                continue
            except Exception as exc:  # noqa: BLE001
                statuses.append(
                    FlowStatus(name=name, status=_STATUS_ERROR, path=path, flow_id=flow_id, detail=str(exc))
                )
                continue

            local_hash = _flow_hash(raw, normalize_flow, flow_to_json)
            remote_hash = _flow_hash(remote_flow.model_dump(mode="json"), normalize_flow, flow_to_json)

            if local_hash == remote_hash:
                statuses.append(FlowStatus(name=name, status=_STATUS_SYNCED, path=path, flow_id=flow_id))
            else:
                remote_updated_at: datetime | None = remote_flow.updated_at
                local_mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                if remote_updated_at and remote_updated_at.tzinfo is None:
                    remote_updated_at = remote_updated_at.replace(tzinfo=timezone.utc)

                status = _STATUS_BEHIND if remote_updated_at and remote_updated_at > local_mtime else _STATUS_AHEAD
                statuses.append(FlowStatus(name=name, status=status, path=path, flow_id=flow_id))

        # ------------------------------------------------------------------ #
        # Remote-only flows                                                   #
        # ------------------------------------------------------------------ #
        if show_remote_only:
            try:
                all_remote = client.list_flows(get_all=True)
                statuses.extend(
                    FlowStatus(
                        name=remote_flow.name,
                        status=_STATUS_REMOTE_ONLY,
                        flow_id=remote_flow.id,
                    )
                    for remote_flow in all_remote
                    if remote_flow.id not in seen_ids
                )
            except Exception as exc:  # noqa: BLE001
                console.print(f"[yellow]Warning:[/yellow] Could not list remote flows: {exc}")
    finally:
        with contextlib.suppress(OSError):
            client.close()

    _render_table(statuses, env_label)

    # Exit 1 when anything is out of sync so CI pipelines can detect drift
    not_clean = [s for s in statuses if s.status not in (_STATUS_SYNCED,)]
    if not_clean:
        raise typer.Exit(1)