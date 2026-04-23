async def verify_tools_by_ids(
    clients: WxOClient,
    snapshot_ids: list[str],
) -> SnapshotListResult:
    """Fetch tools by ID and return only those that still exist on the provider."""
    from lfx.services.adapters.deployment.schema import SnapshotItem, SnapshotListResult

    if not snapshot_ids:
        return SnapshotListResult(snapshots=[])

    unique_ids = list(dict.fromkeys(snapshot_ids))
    try:
        tools = await asyncio.to_thread(clients.tool.get_drafts_by_ids, unique_ids)
    except Exception as exc:  # noqa: BLE001
        raise_as_deployment_error(
            exc,
            error_prefix=ErrorPrefix.LIST,
            log_msg="Unexpected error while verifying wxO tool snapshots by ID",
        )

    snapshots: list[SnapshotItem] = []
    for tool in tools or []:
        if not isinstance(tool, dict) or not tool.get("id"):
            continue
        connections = extract_langflow_connections_binding(tool)
        normalized_connections: dict[str, str] = {
            key: value
            for raw_key, raw_value in connections.items()
            if isinstance(raw_key, str)
            and isinstance(raw_value, str)
            and (key := raw_key.strip())
            and (value := raw_value.strip())
        }

        if len(normalized_connections) < len(connections):
            logger.warning(
                "Tool %s returned malformed langflow connection bindings; defaulting to empty mapping",
                tool["id"],
            )
            provider_data: dict[str, dict[str, str]] = {"connections": {}}
        else:
            provider_data = {"connections": normalized_connections}
        snapshots.append(
            SnapshotItem(
                id=tool["id"],
                name=tool.get("name") or tool["id"],
                provider_data=provider_data,
            )
        )
    return SnapshotListResult(snapshots=snapshots)