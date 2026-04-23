async def install_mcp_config(
    project_id: UUID,
    body: MCPInstallRequest,
    request: Request,
    current_user: CurrentActiveMCPUser,
):
    """Install MCP server configuration for Cursor, Windsurf, or Claude."""
    # Check if the request is coming from a local IP address
    client_ip = get_client_ip(request)
    if not is_local_ip(client_ip):
        raise HTTPException(status_code=500, detail="MCP configuration can only be installed from a local connection")

    removed_servers: list[str] = []  # Track removed servers for reinstallation
    try:
        project = await verify_project_access(project_id, current_user)

        # Check if project requires API key authentication and generate if needed
        generated_api_key = None

        # Determine if we need to generate an API key
        should_generate_api_key = False
        if not get_settings_service().settings.mcp_composer_enabled:
            # When MCP_COMPOSER is disabled, check auth settings or fallback to auto_login setting
            settings_service = get_settings_service()
            if project.auth_settings:
                # Project has auth settings - check if it requires API key
                if project.auth_settings.get("auth_type") == "apikey":
                    should_generate_api_key = True
            elif not settings_service.auth_settings.AUTO_LOGIN:
                # No project auth settings but auto_login is disabled - generate API key
                should_generate_api_key = True
        elif project.auth_settings:
            # When MCP_COMPOSER is enabled, only generate if auth_type is "apikey"
            if project.auth_settings.get("auth_type") == "apikey":
                should_generate_api_key = True

        # Get settings service to build the SSE URL
        settings_service = get_settings_service()
        if settings_service.auth_settings.AUTO_LOGIN and not settings_service.auth_settings.SUPERUSER:
            # Without a superuser fallback, require API key auth for MCP installs.
            should_generate_api_key = True
        settings = settings_service.settings
        host = settings.host or None
        port = settings.port or None
        if not host or not port:
            raise HTTPException(status_code=500, detail="Host and port are not set in settings")

        # Determine command and args based on operating system
        os_type = platform.system()

        use_mcp_composer = should_use_mcp_composer(project)
        connection_urls: list[str]
        transport_mode = (body.transport or "sse").lower()
        if transport_mode not in {"sse", "streamablehttp"}:
            raise HTTPException(status_code=400, detail="Invalid transport. Use 'sse' or 'streamablehttp'.")

        if use_mcp_composer:
            try:
                auth_config = await _get_mcp_composer_auth_config(project)
                await get_or_start_mcp_composer(auth_config, project.name, project_id)
                composer_streamable_http_url = await get_composer_streamable_http_url(project)
                sse_url = await get_composer_sse_url(project)
                connection_urls = [composer_streamable_http_url, sse_url]
            except MCPComposerError as e:
                await logger.aerror(
                    f"Failed to start MCP Composer for project '{project.name}' ({project_id}): {e.message}"
                )
                raise HTTPException(status_code=500, detail=e.message) from e
            except Exception as e:
                error_msg = f"Failed to start MCP Composer for project '{project.name}' ({project_id}): {e!s}"
                await logger.aerror(error_msg)
                error_detail = "Failed to start MCP Composer. See logs for details."
                raise HTTPException(status_code=500, detail=error_detail) from e

            # For OAuth/MCP Composer, use the special format
            settings = get_settings_service().settings
            command = "uvx"
            args = [
                f"mcp-composer{settings.mcp_composer_version}",
                "--mode",
                "http",
                "--endpoint",
                composer_streamable_http_url,
                "--sse-url",
                sse_url,
                "--client_auth_type",
                "oauth",
                "--disable-composer-tools",
            ]
        else:
            # For non-OAuth (API key or no auth), use mcp-proxy
            streamable_http_url = await get_project_streamable_http_url(project_id)
            legacy_sse_url = await get_project_sse_url(project_id)
            command = "uvx"
            args = ["mcp-proxy"]
            # Check if we need to add Langflow API key headers
            # Necessary only when Project API Key Authentication is enabled

            # Generate a Langflow API key for auto-install if needed
            # Only add API key headers for projects with "apikey" auth type (not "none" or OAuth)

            if should_generate_api_key:
                async with session_scope() as api_key_session:
                    api_key_create = ApiKeyCreate(name=f"MCP Server {project.name}")
                    api_key_response = await create_api_key(api_key_session, api_key_create, current_user.id)
                    langflow_api_key = api_key_response.api_key
                    args.extend(["--headers", "x-api-key", langflow_api_key])

            # Add the target URL for mcp-proxy based on requested transport
            proxy_target_url = streamable_http_url if transport_mode == "streamablehttp" else legacy_sse_url
            if transport_mode == "streamablehttp":
                args.extend(["--transport", "streamablehttp"])
            args.append(proxy_target_url)
            connection_urls = [streamable_http_url, legacy_sse_url]

        if os_type == "Windows" and not use_mcp_composer:
            # Only wrap in cmd for Windows when using mcp-proxy
            command = "cmd"
            args = ["/c", "uvx", *args]
            await logger.adebug("Windows detected, using cmd command")

        name = project.name
        server_name = f"lf-{sanitize_mcp_name(name)[: (MAX_MCP_SERVER_NAME_LENGTH - 4)]}"

        # Create the MCP configuration
        server_config: dict[str, Any] = {
            "command": command,
            "args": args,
        }

        mcp_config = {"mcpServers": {server_name: server_config}}

        await logger.adebug("Installing MCP config for project: %s (server name: %s)", project.name, server_name)

        # Get the config file path and check if client is available
        try:
            config_path = await get_config_path(body.client.lower())
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        # Check if the client application is available (config directory exists)
        if not config_path.parent.exists():
            raise HTTPException(
                status_code=400,
                detail=f"{body.client.capitalize()} is not installed on this system. "
                f"Please install {body.client.capitalize()} first.",
            )

        # Create parent directories if they don't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Read existing config if it exists
        existing_config = {}
        if config_path.exists():
            try:
                with config_path.open("r") as f:
                    existing_config = json.load(f)
            except json.JSONDecodeError:
                # If file exists but is invalid JSON, start fresh
                existing_config = {"mcpServers": {}}

        # Ensure mcpServers section exists
        if "mcpServers" not in existing_config:
            existing_config["mcpServers"] = {}

        # Remove stale entries that point to the same Langflow URLs (e.g. after the project is renamed)
        existing_config, removed_servers = remove_server_by_urls(existing_config, connection_urls)

        if removed_servers:
            await logger.adebug("Removed existing MCP servers with same SSE URL for reinstall: %s", removed_servers)

        # Merge new config with existing config
        existing_config["mcpServers"].update(mcp_config["mcpServers"])

        # Write the updated config
        with config_path.open("w") as f:
            json.dump(existing_config, f, indent=2)

    except HTTPException:
        raise
    except Exception as e:
        msg = f"Error installing MCP configuration: {e!s}"
        await logger.aexception(msg)
        raise HTTPException(status_code=500, detail=str(e)) from e
    else:
        action = "reinstalled" if removed_servers else "installed"
        message = f"Successfully {action} MCP configuration for {body.client}"
        if removed_servers:
            message += f" (replaced existing servers: {', '.join(removed_servers)})"
        if generated_api_key:
            auth_type = "API key" if get_settings_service().settings.mcp_composer_enabled else "legacy API key"
            message += f" with {auth_type} authentication (key name: 'MCP Project {project.name} - {body.client}')"
        await logger.adebug(message)
        return {"message": message}