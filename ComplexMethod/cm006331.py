async def _bind_existing_tools_for_create(
    *,
    clients: WxOClient,
    existing_tool_bindings: dict[str, list[str]],
    operation_to_provider_app_id: dict[str, str],
    resolved_connections: dict[str, str],
    original_tools: dict[str, dict[str, Any]],
) -> None:
    tool_ids = list(existing_tool_bindings.keys())
    tools = await asyncio.to_thread(clients.tool.get_drafts_by_ids, tool_ids)
    tool_by_id = {str(tool.get("id")): tool for tool in tools if isinstance(tool, dict) and tool.get("id")}
    missing_tool_ids = [tool_id for tool_id in tool_ids if tool_id not in tool_by_id]
    if missing_tool_ids:
        missing_ids = ", ".join(missing_tool_ids)
        msg = f"Snapshot tool(s) not found: {missing_ids}"
        raise InvalidContentError(message=msg)

    tool_updates: list[tuple[str, dict[str, Any]]] = []
    for tool_id in tool_ids:
        tool = tool_by_id[tool_id]
        verify_langflow_owned(tool, tool_id=tool_id)

        original_tool = to_writable_tool_payload(tool)
        original_tools[tool_id] = original_tool
        writable_tool = copy.deepcopy(original_tool)
        connections = ensure_langflow_connections_binding(writable_tool)

        for operation_app_id in existing_tool_bindings[tool_id]:
            provider_app_id = operation_to_provider_app_id.get(operation_app_id)
            if not provider_app_id:
                msg = f"No provider app id available for operation app_id '{operation_app_id}'."
                raise InvalidContentError(message=msg)
            connection_id = resolved_connections.get(provider_app_id)
            if not connection_id:
                msg = f"No resolved connection id available for app_id '{operation_app_id}'."
                raise InvalidContentError(message=msg)
            connections[provider_app_id] = connection_id

        tool_updates.append((tool_id, writable_tool))

    await asyncio.gather(
        *(
            retry_update(asyncio.to_thread, clients.tool.update, tool_id, writable_tool)
            for tool_id, writable_tool in tool_updates
        )
    )