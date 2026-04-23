async def init_mcp_servers():
    """Initialize MCP servers for all projects."""
    try:
        settings_service = get_settings_service()

        async with session_scope() as session:
            projects = (await session.exec(select(Folder))).all()

            for project in projects:
                try:
                    # Auto-enable API key auth for projects without auth settings or with "none" auth
                    # when AUTO_LOGIN is false
                    if not settings_service.auth_settings.AUTO_LOGIN:
                        should_update_to_apikey = False

                        if not project.auth_settings:
                            # No auth settings at all
                            should_update_to_apikey = True
                        # Check if existing auth settings have auth_type "none"
                        elif project.auth_settings.get("auth_type") == "none":
                            should_update_to_apikey = True

                        if should_update_to_apikey:
                            default_auth = {"auth_type": "apikey"}
                            project.auth_settings = encrypt_auth_settings(default_auth)
                            session.add(project)
                            await logger.ainfo(
                                f"Auto-enabled API key authentication for existing project {project.name} "
                                f"({project.id}) due to AUTO_LOGIN=false"
                            )

                    # WARN: If oauth projects exist in the database and the MCP Composer is disabled,
                    # these projects will be reset to "apikey" or "none" authentication, erasing all oauth settings.
                    if (
                        not settings_service.settings.mcp_composer_enabled
                        and project.auth_settings
                        and project.auth_settings.get("auth_type") == "oauth"
                    ):
                        # Reset OAuth projects to appropriate auth type based on AUTO_LOGIN setting
                        fallback_auth_type = "apikey" if not settings_service.auth_settings.AUTO_LOGIN else "none"
                        clean_auth = AuthSettings(auth_type=fallback_auth_type)
                        project.auth_settings = clean_auth.model_dump(exclude_none=True)
                        session.add(project)
                        await logger.adebug(
                            f"Updated OAuth project {project.name} ({project.id}) to use {fallback_auth_type} "
                            f"authentication because MCP Composer is disabled"
                        )

                    get_project_sse(project.id)
                    get_project_mcp_server(project.id)
                    await logger.adebug(f"Initialized MCP server for project: {project.name} ({project.id})")

                    # Only register with MCP Composer if OAuth authentication is configured
                    if get_settings_service().settings.mcp_composer_enabled and project.auth_settings:
                        auth_type = project.auth_settings.get("auth_type")
                        if auth_type == "oauth":
                            await logger.adebug(
                                f"Starting MCP Composer for OAuth project {project.name} ({project.id}) on startup"
                            )
                            await register_project_with_composer(project)

                except Exception as e:  # noqa: BLE001
                    msg = f"Failed to initialize MCP server for project {project.id}: {e}"
                    await logger.aexception(msg)
                    # Continue to next project even if this one fails

            # Auto-configure starter projects with MCP server settings if enabled
            await auto_configure_starter_projects_mcp(session)

    except Exception as e:  # noqa: BLE001
        msg = f"Failed to initialize MCP servers: {e}"
        await logger.aexception(msg)