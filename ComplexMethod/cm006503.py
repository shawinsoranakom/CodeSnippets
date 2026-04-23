async def cleanup_mcp_on_delete(
    project,
    project_id: UUID,
    current_user,
    session,
) -> None:
    """Clean up MCP resources when a project is deleted.

    Stops the MCP Composer if the project uses OAuth, and removes the
    corresponding MCP server entry if auto-add was enabled.
    """
    # Stop MCP Composer if project used OAuth
    if project.auth_settings and project.auth_settings.get("auth_type") == "oauth":
        try:
            mcp_composer_service: MCPComposerService = cast(
                MCPComposerService, get_service(ServiceType.MCP_COMPOSER_SERVICE)
            )
            await mcp_composer_service.stop_project_composer(str(project_id))
            await logger.adebug("Stopped MCP Composer for deleted OAuth project %s (%s)", project.name, project_id)
        except Exception as e:  # noqa: BLE001
            await logger.aerror("Failed to stop MCP Composer for deleted project %s: %s", project_id, e)

    # Delete corresponding MCP server if auto-add was enabled
    if get_settings_service().settings.add_projects_to_mcp_servers:
        try:
            validation_result = await validate_mcp_server_for_project(
                project_id,
                project.name,
                current_user,
                session,
                get_storage_service(),
                get_settings_service(),
                operation="delete",
            )

            if validation_result.server_exists and validation_result.project_id_matches:
                await update_server(
                    validation_result.server_name,
                    {},
                    current_user,
                    session,
                    get_storage_service(),
                    get_settings_service(),
                    delete=True,
                )
                await logger.adebug(
                    "Deleted MCP server %s for deleted project %s (%s)",
                    validation_result.server_name,
                    project.name,
                    project_id,
                )
            elif validation_result.server_exists and not validation_result.project_id_matches:
                await logger.adebug(
                    "MCP server '%s' exists but belongs to different project, skipping deletion",
                    validation_result.server_name,
                )
            else:
                await logger.adebug("No MCP server found for deleted project %s (%s)", project.name, project_id)

        except Exception as e:  # noqa: BLE001
            await logger.awarning("Failed to handle MCP server cleanup for deleted project %s: %s", project_id, e)