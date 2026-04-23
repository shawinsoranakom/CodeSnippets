async def validate_mcp_server_for_project(
    project_id: UUID,
    project_name: str,
    user,
    session,
    storage_service,
    settings_service,
    operation: str = "create",
) -> MCPServerValidationResult:
    """Validate MCP server for a project operation.

    Args:
        project_id: The project UUID
        project_name: The project name
        user: The user performing the operation
        session: Database session
        storage_service: Storage service
        settings_service: Settings service
        operation: Operation type ("create", "update", "delete")

    Returns:
        MCPServerValidationResult with validation details
    """
    # Generate server name that would be used for this project
    server_name = f"lf-{sanitize_mcp_name(project_name)[: (MAX_MCP_SERVER_NAME_LENGTH - 4)]}"

    try:
        existing_servers = await get_server_list(user, session, storage_service, settings_service)

        if server_name not in existing_servers.get("mcpServers", {}):
            # Server doesn't exist
            return MCPServerValidationResult(
                project_id_matches=False,
                server_exists=False,
                server_name=server_name,
            )

        # Server exists - check if project ID matches
        existing_server_config = existing_servers["mcpServers"][server_name]
        existing_args = existing_server_config.get("args", [])
        project_id_matches = False

        if existing_args:
            # SSE URL is typically the last argument
            # TODO: Better way Required to check the postion of the SSE URL in the args
            existing_sse_urls = await extract_urls_from_strings(existing_args)
            for existing_sse_url in existing_sse_urls:
                if str(project_id) in existing_sse_url:
                    project_id_matches = True
                    break
        else:
            project_id_matches = False

        # Generate appropriate conflict message based on operation
        conflict_message = ""
        if not project_id_matches:
            if operation == "create":
                conflict_message = (
                    f"MCP server name conflict: '{server_name}' already exists "
                    f"for a different project. Cannot create MCP server for project "
                    f"'{project_name}' (ID: {project_id})"
                )
            elif operation == "update":
                conflict_message = (
                    f"MCP server name conflict: '{server_name}' exists for a different project. "
                    f"Cannot update MCP server for project '{project_name}' (ID: {project_id})"
                )
            elif operation == "delete":
                conflict_message = (
                    f"MCP server '{server_name}' exists for a different project. "
                    f"Cannot delete MCP server for project '{project_name}' (ID: {project_id})"
                )

        return MCPServerValidationResult(
            server_exists=True,
            project_id_matches=project_id_matches,
            server_name=server_name,
            existing_config=existing_server_config,
            conflict_message=conflict_message,
        )

    except Exception as e:  # noqa: BLE001
        await logger.awarning(f"Could not validate MCP server for project {project_id}: {e}")
        # Return result allowing operation to proceed on validation failure
        return MCPServerValidationResult(
            project_id_matches=False,
            server_exists=False,
            server_name=server_name,
        )