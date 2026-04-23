async def handle_mcp_server_rename(
    existing_project,
    old_project_name: str,
    new_project_name: str,
    current_user,
    session,
) -> None:
    """Handle MCP server name update when a project is renamed.

    Validates old and new server names, checks for conflicts, and performs
    the rename (delete old + create new) if needed.

    Raises HTTPException on name conflicts.
    """
    try:
        old_validation = await validate_mcp_server_for_project(
            existing_project.id,
            old_project_name,
            current_user,
            session,
            get_storage_service(),
            get_settings_service(),
            operation="update",
        )

        new_validation = await validate_mcp_server_for_project(
            existing_project.id,
            new_project_name,
            current_user,
            session,
            get_storage_service(),
            get_settings_service(),
            operation="update",
        )

        if old_validation.server_name != new_validation.server_name:
            if new_validation.has_conflict:
                await logger.aerror(new_validation.conflict_message)
                raise HTTPException(
                    status_code=409,
                    detail=new_validation.conflict_message,
                )

            if old_validation.server_exists and old_validation.project_id_matches:
                await update_server(
                    old_validation.server_name,
                    {},
                    current_user,
                    session,
                    get_storage_service(),
                    get_settings_service(),
                    delete=True,
                )

                await update_server(
                    new_validation.server_name,
                    old_validation.existing_config or {},
                    current_user,
                    session,
                    get_storage_service(),
                    get_settings_service(),
                )

                await logger.adebug(
                    "Updated MCP server name from %s to %s",
                    old_validation.server_name,
                    new_validation.server_name,
                )
            else:
                await logger.adebug(
                    "Old MCP server '%s' not found for this project, skipping rename",
                    old_validation.server_name,
                )

    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        await logger.awarning("Failed to handle MCP server name update for project rename: %s", e)