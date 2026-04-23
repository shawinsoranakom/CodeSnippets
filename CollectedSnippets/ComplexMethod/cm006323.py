async def update_existing_tool_connection_bindings(
    *,
    clients: WxOClient,
    existing_target_tool_ids: list[str],
    resolved_connections: dict[str, str],
    original_tools: dict[str, dict[str, Any]],
) -> None:
    """Apply resolved connection bindings to existing tools.

    Captures original writable payloads for rollback before any update call.
    Raises ``InvalidContentError`` when any expected tool id is missing.
    """
    if not existing_target_tool_ids:
        return

    tools = await asyncio.to_thread(clients.tool.get_drafts_by_ids, existing_target_tool_ids)
    tool_by_id = {str(tool.get("id")): tool for tool in tools if isinstance(tool, dict) and tool.get("id")}
    missing_tool_ids = [tool_id for tool_id in existing_target_tool_ids if tool_id not in tool_by_id]
    if missing_tool_ids:
        missing_ids = ", ".join(missing_tool_ids)
        msg = f"Snapshot tool(s) not found: {missing_ids}"
        raise InvalidContentError(message=msg)

    tool_updates: list[tuple[str, dict[str, Any]]] = []
    for tool_id in existing_target_tool_ids:
        tool = tool_by_id[tool_id]
        verify_langflow_owned(tool, tool_id=tool_id)

        original_tool = to_writable_tool_payload(tool)
        original_tools[tool_id] = original_tool
        writable_tool = copy.deepcopy(original_tool)
        connections = ensure_langflow_connections_binding(writable_tool)
        connections.update(resolved_connections)
        tool_updates.append((tool_id, writable_tool))

    await asyncio.gather(
        *(
            retry_create(asyncio.to_thread, clients.tool.update, tool_id, writable_tool)
            for tool_id, writable_tool in tool_updates
        )
    )