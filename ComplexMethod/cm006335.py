async def _apply_tool_renames(
    *,
    clients: WxOClient,
    agent_tool_ids: list[str],
    tool_renames: dict[str, str],
    original_tools: dict[str, dict[str, Any]],
) -> None:
    """Rename tools on the provider with safety checks.

    Guards against destructive operations on tools we don't own:
    1. Tool must be attached to this agent (tool_id in agent_tool_ids).
    2. Tool must be a Langflow-managed tool (has ``binding.langflow``).
    3. Tool must exist on the provider.

    Captures original tool payloads in ``original_tools`` for rollback.
    """
    if not tool_renames:
        return

    # Verify all tools belong to this agent before fetching
    for tool_id in tool_renames:
        if tool_id not in agent_tool_ids:
            msg = f"Cannot rename tool '{tool_id}': not attached to this agent."
            raise InvalidContentError(message=msg)

    tool_ids = list(tool_renames.keys())
    tools = await asyncio.to_thread(clients.tool.get_drafts_by_ids, tool_ids)
    tool_by_id = {str(t.get("id")): t for t in tools if isinstance(t, dict) and t.get("id")}

    missing = [tid for tid in tool_ids if tid not in tool_by_id]
    if missing:
        msg = f"Cannot rename tool(s) not found in provider: {', '.join(missing)}"
        raise InvalidContentError(message=msg)

    tool_updates: list[tuple[str, dict[str, Any]]] = []
    for tool_id, new_name in tool_renames.items():
        tool = tool_by_id[tool_id]

        verify_langflow_owned(tool, tool_id=tool_id)

        # Capture original for rollback (if not already captured by delta updates)
        if tool_id not in original_tools:
            original_tools[tool_id] = to_writable_tool_payload(tool)

        # Use the current provider payload as rename base so we preserve
        # connection changes applied earlier in this update transaction.
        writable = to_writable_tool_payload(tool)
        writable["name"] = new_name
        writable["display_name"] = new_name
        tool_updates.append((tool_id, writable))

    await asyncio.gather(
        *(retry_update(asyncio.to_thread, clients.tool.update, tool_id, writable) for tool_id, writable in tool_updates)
    )
    logger.debug("_apply_tool_renames: renamed %d tools: %s", len(tool_updates), tool_renames)