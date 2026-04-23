async def check_installed_mcp_servers(
    project_id: UUID,
    current_user: CurrentActiveMCPUser,
):
    """Check if MCP server configuration is installed for this project in Cursor, Windsurf, or Claude."""
    try:
        # Verify project exists and user has access
        async with session_scope() as session:
            project = (
                await session.exec(select(Folder).where(Folder.id == project_id, Folder.user_id == current_user.id))
            ).first()

            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

        project = await verify_project_access(project_id, current_user)
        if should_use_mcp_composer(project):
            project_streamable_url = await get_composer_streamable_http_url(project)
            project_sse_url = await get_composer_sse_url(project)
        else:
            project_streamable_url = await get_project_streamable_http_url(project_id)
            project_sse_url = await get_project_sse_url(project_id)

        await logger.adebug(
            "Checking for installed MCP servers for project: %s (SSE URL: %s)", project.name, project_sse_url
        )

        # Define supported clients
        clients = ["cursor", "windsurf", "claude"]
        results = []

        for client_name in clients:
            try:
                # Get config path for this client
                config_path = await get_config_path(client_name)
                available = config_path.parent.exists()
                installed = False

                await logger.adebug("Checking %s config at: %s (exists: %s)", client_name, config_path, available)

                # If config file exists, check if project is installed
                if available:
                    try:
                        with config_path.open("r") as f:
                            config_data = json.load(f)
                        if config_contains_server_url(config_data, [project_streamable_url, project_sse_url]):
                            await logger.adebug(
                                "Found %s config with matching URL for project %s", client_name, project.name
                            )
                            installed = True
                        else:
                            await logger.adebug(
                                "%s config exists but no server with URL: %s (available servers: %s)",
                                client_name,
                                project_sse_url,
                                list(config_data.get("mcpServers", {}).keys()),
                            )
                    except FileNotFoundError:
                        await logger.adebug(
                            "%s config file not found at %s (directory exists, app installed but not configured)",
                            client_name,
                            config_path,
                        )
                        # available stays True, installed stays False — app is installed but not yet configured
                    except json.JSONDecodeError:
                        await logger.awarning("Failed to parse %s config JSON at: %s", client_name, config_path)
                        # available is True but installed remains False due to parse error
                else:
                    await logger.adebug("%s config path not found or doesn't exist: %s", client_name, config_path)

                # Add result for this client
                results.append({"name": client_name, "installed": installed, "available": available})

            except Exception as e:  # noqa: BLE001
                # If there's an error getting config path or checking the client,
                # mark it as not available and not installed
                await logger.awarning("Error checking %s configuration: %s", client_name, str(e))
                results.append({"name": client_name, "installed": False, "available": False})

    except Exception as e:
        msg = f"Error checking MCP configuration: {e!s}"
        await logger.aexception(msg)
        raise HTTPException(status_code=500, detail=str(e)) from e
    return results