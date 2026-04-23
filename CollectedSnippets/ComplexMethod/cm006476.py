async def update_project(
    *,
    session: DbSession,
    project_id: UUID,
    project: FolderUpdate,  # Assuming FolderUpdate is a Pydantic model defining updatable fields
    current_user: CurrentActiveUser,
    background_tasks: BackgroundTasks,
):
    try:
        existing_project = (
            await session.exec(select(Folder).where(Folder.id == project_id, Folder.user_id == current_user.id))
        ).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    if not existing_project:
        raise HTTPException(status_code=404, detail="Project not found")

    result = await session.exec(
        select(Flow.id, Flow.is_component).where(Flow.folder_id == existing_project.id, Flow.user_id == current_user.id)
    )
    flows_and_components = result.all()

    project.flows = [flow_id for flow_id, is_component in flows_and_components if not is_component]
    project.components = [flow_id for flow_id, is_component in flows_and_components if is_component]

    try:
        # Track if MCP Composer needs to be started or stopped
        should_start_mcp_composer = False
        should_stop_mcp_composer = False

        # Check if auth_settings is being updated
        if "auth_settings" in project.model_fields_set:  # Check if auth_settings was explicitly provided
            auth_result = handle_auth_settings_update(
                existing_project=existing_project,
                new_auth_settings=project.auth_settings,
            )

            should_start_mcp_composer = auth_result["should_start_composer"]
            should_stop_mcp_composer = auth_result["should_stop_composer"]

        # Handle project rename and corresponding MCP server rename
        if project.name and project.name != existing_project.name:
            old_project_name = existing_project.name
            existing_project.name = project.name

            if get_settings_service().settings.add_projects_to_mcp_servers:
                await handle_mcp_server_rename(existing_project, old_project_name, project.name, current_user, session)

        if project.description is not None:
            existing_project.description = project.description

        if project.parent_id is not None:
            existing_project.parent_id = project.parent_id

        session.add(existing_project)
        await session.flush()
        await session.refresh(existing_project)

        # Start MCP Composer if auth changed to OAuth
        if should_start_mcp_composer:
            await logger.adebug(
                "Auth settings changed to OAuth for project %s (%s), starting MCP Composer",
                existing_project.name,
                existing_project.id,
            )
            background_tasks.add_task(register_project_with_composer, existing_project)

        # Stop MCP Composer if auth changed FROM OAuth to something else
        elif should_stop_mcp_composer:
            await logger.ainfo(
                "Auth settings changed from OAuth for project %s (%s), stopping MCP Composer",
                existing_project.name,
                existing_project.id,
            )

            mcp_composer_service: MCPComposerService = cast(
                MCPComposerService, get_service(ServiceType.MCP_COMPOSER_SERVICE)
            )
            await mcp_composer_service.stop_project_composer(str(existing_project.id))

        concat_project_components = project.components + project.flows

        flows_ids = (await session.exec(select(Flow.id).where(Flow.folder_id == existing_project.id))).all()

        excluded_flows = list(set(flows_ids) - set(project.flows))

        my_collection_project = (await session.exec(select(Folder).where(Folder.name == DEFAULT_FOLDER_NAME))).first()
        if my_collection_project:
            update_statement_my_collection = (
                update(Flow).where(Flow.id.in_(excluded_flows)).values(folder_id=my_collection_project.id)  # type: ignore[attr-defined]
            )
            await session.exec(update_statement_my_collection)

        if concat_project_components:
            update_statement_components = (
                update(Flow).where(Flow.id.in_(concat_project_components)).values(folder_id=existing_project.id)  # type: ignore[attr-defined]
            )
            await session.exec(update_statement_components)

        # Convert to FolderRead while session is still active to avoid detached instance errors
        folder_read = FolderRead.model_validate(existing_project, from_attributes=True)

    except HTTPException:
        # Re-raise HTTP exceptions (like 409 conflicts) without modification
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return folder_read