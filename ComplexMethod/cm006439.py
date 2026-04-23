async def _build_project_tools_response(
    project_id: UUID,
    current_user: CurrentActiveMCPUser,
    *,
    mcp_enabled: bool,
) -> MCPProjectResponse:
    """Return tool metadata for a project."""
    tools: list[MCPSettings] = []
    try:
        async with session_scope() as session:
            # Fetch the project first to verify it exists and belongs to the current user
            project = (
                await session.exec(
                    select(Folder)
                    .options(selectinload(Folder.flows))
                    .where(Folder.id == project_id, Folder.user_id == current_user.id)
                )
            ).first()

            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            # Query flows in the project
            flows_query = select(Flow).where(Flow.folder_id == project_id, Flow.is_component == False)  # noqa: E712

            # Optionally filter for MCP-enabled flows only
            if mcp_enabled:
                flows_query = flows_query.where(Flow.mcp_enabled == True)  # noqa: E712

            flows = (await session.exec(flows_query)).all()

            for flow in flows:
                if flow.user_id is None:
                    continue

                # Format the flow name according to MCP conventions (snake_case)
                flow_name = sanitize_mcp_name(flow.name)

                # Use action_name and action_description if available, otherwise use defaults
                name = sanitize_mcp_name(flow.action_name) if flow.action_name else flow_name
                description = flow.action_description or (
                    flow.description if flow.description else f"Tool generated from flow: {flow_name}"
                )
                try:
                    tool = MCPSettings(
                        id=flow.id,
                        action_name=name,
                        action_description=description,
                        mcp_enabled=flow.mcp_enabled,
                        # inputSchema=json_schema_from_flow(flow),
                        name=flow.name,
                        description=flow.description,
                    )
                    tools.append(tool)
                except Exception as e:  # noqa: BLE001
                    msg = f"Error in listing project tools: {e!s} from flow: {name}"
                    await logger.awarning(msg)
                    continue

            # Get project-level auth settings but mask sensitive fields for security
            auth_settings = None
            if project.auth_settings:
                # Decrypt to get the settings structure
                decrypted_settings = decrypt_auth_settings(project.auth_settings)
                if decrypted_settings:
                    # Mask sensitive fields before sending to frontend
                    masked_settings = decrypted_settings.copy()
                    if masked_settings.get("oauth_client_secret"):
                        masked_settings["oauth_client_secret"] = "*******"  # noqa: S105
                    if masked_settings.get("api_key"):
                        masked_settings["api_key"] = "*******"
                    auth_settings = AuthSettings(**masked_settings)

    except Exception as e:
        msg = f"Error listing project tools: {e!s}"
        await logger.aexception(msg)
        raise HTTPException(status_code=500, detail=str(e)) from e

    return MCPProjectResponse(tools=tools, auth_settings=auth_settings)