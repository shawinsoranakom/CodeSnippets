async def auto_configure_starter_projects_mcp(session):
    """Auto-configure MCP servers for starter projects for all users at startup."""
    # Check if auto-configure is enabled
    settings_service = get_settings_service()
    await logger.adebug("Starting auto-configure starter projects MCP")
    if not settings_service.settings.add_projects_to_mcp_servers:
        await logger.adebug("Auto-Configure MCP servers disabled, skipping starter project MCP configuration")
        return
    await logger.adebug(
        f"Auto-configure settings: add_projects_to_mcp_servers="
        f"{settings_service.settings.add_projects_to_mcp_servers}, "
        f"create_starter_projects={settings_service.settings.create_starter_projects}, "
        f"update_starter_projects={settings_service.settings.update_starter_projects}"
    )

    try:
        # Get all users in the system
        users = (await session.exec(select(User))).all()
        await logger.adebug(f"Found {len(users)} users in the system")
        if not users:
            await logger.adebug("No users found, skipping starter project MCP configuration")
            return

        # Add starter projects to each user's MCP server configuration
        total_servers_added = 0
        for user in users:
            await logger.adebug(f"Processing user: {user.username} (ID: {user.id})")
            try:
                # First, let's see what folders this user has
                all_user_folders = (await session.exec(select(Folder).where(Folder.user_id == user.id))).all()
                folder_names = [f.name for f in all_user_folders]
                await logger.adebug(f"User {user.username} has folders: {folder_names}")

                # Find THIS USER'S own starter projects folder
                # Each user has their own "Starter Projects" folder with unique ID
                user_starter_folder = (
                    await session.exec(
                        select(Folder).where(
                            Folder.name == DEFAULT_FOLDER_NAME,
                            Folder.user_id == user.id,  # Each user has their own!
                        )
                    )
                ).first()
                if not user_starter_folder:
                    await logger.adebug(
                        f"No starter projects folder ('{DEFAULT_FOLDER_NAME}') found for user {user.username}, skipping"
                    )
                    # Log what folders this user does have for debugging
                    await logger.adebug(f"User {user.username} available folders: {folder_names}")
                    continue

                await logger.adebug(
                    f"Found starter folder '{user_starter_folder.name}' for {user.username}: "
                    f"ID={user_starter_folder.id}"
                )

                # Configure MCP settings for flows in THIS USER'S starter folder
                flows_query = select(Flow).where(
                    Flow.folder_id == user_starter_folder.id,
                    Flow.is_component == False,  # noqa: E712
                )
                user_starter_flows = (await session.exec(flows_query)).all()

                # Enable MCP for starter flows if not already configured
                flows_configured = 0
                for flow in user_starter_flows:
                    if flow.mcp_enabled is None:
                        flow.mcp_enabled = True
                        if not flow.action_name:
                            flow.action_name = sanitize_mcp_name(flow.name)
                        if not flow.action_description:
                            flow.action_description = flow.description or f"Starter project: {flow.name}"
                        flow.updated_at = datetime.now(timezone.utc)
                        session.add(flow)
                        flows_configured += 1

                if flows_configured > 0:
                    await logger.adebug(f"Enabled MCP for {flows_configured} starter flows for user {user.username}")

                # Validate MCP server for this starter projects folder
                validation_result = await validate_mcp_server_for_project(
                    user_starter_folder.id,
                    DEFAULT_FOLDER_NAME,
                    user,
                    session,
                    get_storage_service(),
                    settings_service,
                    operation="create",
                )

                # Skip if server already exists for this starter projects folder
                if validation_result.should_skip:
                    # Check if the URL needs updating (e.g., server port changed at restart)
                    expected_url = await get_project_streamable_http_url(user_starter_folder.id)
                    existing_config = validation_result.existing_config or {}
                    existing_args = existing_config.get("args", [])
                    existing_urls = await extract_urls_from_strings(existing_args)

                    if any(expected_url == url for url in existing_urls):
                        await logger.adebug(
                            f"MCP server '{validation_result.server_name}' already exists and is correctly "
                            f"configured for user {user.username}'s starter projects (project ID: "
                            f"{user_starter_folder.id}), skipping"
                        )
                        continue  # Skip this user since server already exists for the same project

                    # URL has changed (e.g., server restarted on a different port), fall through to update
                    await logger.adebug(
                        f"MCP server '{validation_result.server_name}' exists for user {user.username}'s "
                        f"starter projects but URL has changed (was: {existing_urls}, now: {expected_url}), updating"
                    )

                server_name = validation_result.server_name

                # Set up THIS USER'S starter folder authentication (same as new projects)
                # If AUTO_LOGIN is false, automatically enable API key authentication
                default_auth = {"auth_type": "none"}
                await logger.adebug("Settings service auth settings: [REDACTED]")
                await logger.adebug("User starter folder auth settings: [REDACTED]")
                if (
                    not user_starter_folder.auth_settings
                    and settings_service.auth_settings.AUTO_LOGIN
                    and not settings_service.auth_settings.SUPERUSER
                ):
                    default_auth = {"auth_type": "apikey"}
                    user_starter_folder.auth_settings = encrypt_auth_settings(default_auth)
                    await logger.adebug(
                        "AUTO_LOGIN enabled without SUPERUSER; forcing API key auth for starter folder %s",
                        user.username,
                    )
                elif not settings_service.auth_settings.AUTO_LOGIN and not user_starter_folder.auth_settings:
                    default_auth = {"auth_type": "apikey"}
                    user_starter_folder.auth_settings = encrypt_auth_settings(default_auth)
                    await logger.adebug(f"Set up auth settings for user {user.username}'s starter folder")
                elif user_starter_folder.auth_settings:
                    default_auth = user_starter_folder.auth_settings

                # Create API key for this user to access their own starter projects
                api_key_name = f"MCP Project {DEFAULT_FOLDER_NAME} - {user.username}"
                unmasked_api_key = await create_api_key(session, ApiKeyCreate(name=api_key_name), user.id)

                # Build connection URLs for THIS USER'S starter folder (unique ID per user)
                streamable_http_url = await get_project_streamable_http_url(user_starter_folder.id)

                # Prepare server config (similar to new project creation)
                if default_auth.get("auth_type", "none") == "apikey":
                    command = "uvx"
                    args = [
                        "mcp-proxy",
                        "--transport",
                        "streamablehttp",
                        "--headers",
                        "x-api-key",
                        unmasked_api_key.api_key,
                        streamable_http_url,
                    ]
                elif default_auth.get("auth_type", "none") == "oauth":
                    msg = "OAuth authentication is not yet implemented for MCP server creation during project creation."
                    logger.warning(msg)
                    raise HTTPException(status_code=501, detail=msg)
                else:  # default_auth_type == "none"
                    # No authentication - direct connection
                    command = "uvx"
                    args = [
                        "mcp-proxy",
                        "--transport",
                        "streamablehttp",
                        streamable_http_url,
                    ]
                server_config = {"command": command, "args": args}

                # Add to user's MCP servers configuration
                await logger.adebug(f"Adding MCP server '{server_name}' for user {user.username}")
                await update_server(
                    server_name,
                    server_config,
                    user,
                    session,
                    get_storage_service(),
                    settings_service,
                )

                total_servers_added += 1
                await logger.adebug(f"Added starter projects MCP server for user: {user.username}")

            except Exception as e:  # noqa: BLE001
                # If server already exists or other issues, just log and continue
                await logger.aerror(f"Could not add starter projects MCP server for user {user.username}: {e}")
                continue

        await session.commit()

        if total_servers_added > 0:
            await logger.adebug(f"Added starter projects MCP servers for {total_servers_added} users")
        else:
            await logger.adebug("No new starter project MCP servers were added")

    except Exception as e:  # noqa: BLE001
        await logger.aerror(f"Failed to auto-configure starter projects MCP servers: {e}")