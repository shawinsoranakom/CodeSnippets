async def handle_list_tools(project_id=None, *, mcp_enabled_only=False):
    """Handle listing tools for MCP.

    Args:
        project_id: Optional project ID to filter tools by project
        mcp_enabled_only: Whether to filter for MCP-enabled flows only
    """
    tools = []
    try:
        async with session_scope() as session:
            # Build query based on parameters
            if project_id:
                # Filter flows by project and optionally by MCP enabled status
                flows_query = select(Flow).where(Flow.folder_id == project_id, Flow.is_component == False)  # noqa: E712
                if mcp_enabled_only:
                    flows_query = flows_query.where(Flow.mcp_enabled == True)  # noqa: E712
            else:
                # Get all flows
                flows_query = select(Flow)

            flows = (await session.exec(flows_query)).all()

            existing_names = set()
            for flow in flows:
                if flow.user_id is None:
                    continue

                # For project-specific tools, use action names if available
                if project_id:
                    base_name = (
                        sanitize_mcp_name(flow.action_name) if flow.action_name else sanitize_mcp_name(flow.name)
                    )
                    name = get_unique_name(base_name, MAX_MCP_TOOL_NAME_LENGTH, existing_names)
                    description = flow.action_description or (
                        flow.description if flow.description else f"Tool generated from flow: {name}"
                    )
                else:
                    # For global tools, use simple sanitized names
                    base_name = sanitize_mcp_name(flow.name)
                    name = base_name[:MAX_MCP_TOOL_NAME_LENGTH]
                    if name in existing_names:
                        i = 1
                        while True:
                            suffix = f"_{i}"
                            truncated_base = base_name[: MAX_MCP_TOOL_NAME_LENGTH - len(suffix)]
                            candidate = f"{truncated_base}{suffix}"
                            if candidate not in existing_names:
                                name = candidate
                                break
                            i += 1
                    description = (
                        f"{flow.id}: {flow.description}" if flow.description else f"Tool generated from flow: {name}"
                    )

                try:
                    tool = types.Tool(
                        name=name,
                        description=description,
                        inputSchema=json_schema_from_flow(flow),
                    )
                    tools.append(tool)
                    existing_names.add(name)
                except Exception as e:  # noqa: BLE001
                    msg = f"Error in listing tools: {e!s} from flow: {base_name}"
                    await logger.awarning(msg)
                    continue
    except Exception as e:
        msg = f"Error in listing tools: {e!s}"
        await logger.aexception(msg)
        raise
    return tools