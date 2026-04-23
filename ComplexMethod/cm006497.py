async def handle_list_resources(project_id=None):
    """Handle listing resources for MCP.

    Args:
        project_id: Optional project ID to filter resources by project
    """
    resources = []
    try:
        storage_service = get_storage_service()
        settings_service = get_settings_service()

        # Build full URL from settings
        host = getattr(settings_service.settings, "host", "localhost")
        port = getattr(settings_service.settings, "port", 3000)

        base_url = f"http://{host}:{port}".rstrip("/")
        try:
            current_user = current_user_ctx.get()
        except Exception as e:  # noqa: BLE001
            msg = f"Error getting current user: {e!s}"
            await logger.aexception(msg)
            current_user = None
        async with session_scope() as session:
            # Build query based on whether project_id is provided
            flows_query = select(Flow).where(Flow.folder_id == project_id) if project_id else select(Flow)

            flows = (await session.exec(flows_query)).all()

            for flow in flows:
                if flow.id:
                    try:
                        files = await storage_service.list_files(flow_id=str(flow.id))
                        for file_name in files:
                            # URL encode the filename
                            safe_filename = quote(file_name)
                            resource = types.Resource(
                                uri=f"{base_url}/api/v1/files/download/{flow.id}/{safe_filename}",
                                name=file_name,
                                description=f"File in flow: {flow.name}",
                                mimeType=build_content_type_from_extension(file_name),
                            )
                            resources.append(resource)
                    except FileNotFoundError as e:
                        msg = f"Error listing files for flow {flow.id}: {e}"
                        await logger.adebug(msg)
                        continue
            ####################################################
            # When a user uploads a file inside a flow
            # (e.g., via the File Read component),
            # it hits /api/v2/files (POST),
            # which saves files at the user-level.
            # So the above query for flow files is not enough.
            # So we list all user files for the current user.
            # This is not good. We need to fix this for 1.8.0.
            ###################################################
            if current_user:
                user_files_stmt = select(UserFile).where(UserFile.user_id == current_user.id)
                user_files = (await session.exec(user_files_stmt)).all()
                for user_file in user_files:
                    stored_path = getattr(user_file, "path", "") or ""
                    stored_filename = Path(stored_path).name if stored_path else user_file.name
                    safe_filename = quote(stored_filename)
                    if stored_filename.startswith(f"{MCP_SERVERS_FILE}_{current_user.id}"):
                        # reserved file name for langflow MCP server config file(s)
                        continue
                    description = getattr(user_file, "provider", None) or "User file uploaded via File Manager"
                    resource = types.Resource(
                        uri=f"{base_url}/api/v1/files/download/{current_user.id}/{safe_filename}",
                        name=stored_filename,
                        description=description,
                        mimeType=build_content_type_from_extension(stored_filename),
                    )
                    resources.append(resource)
    except Exception as e:
        msg = f"Error in listing resources: {e!s}"
        await logger.aexception(msg)
        raise
    return resources