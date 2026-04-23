async def create_project(
    *,
    session: DbSession,
    project: FolderCreate,
    current_user: CurrentActiveUser,
):
    try:
        new_project = Folder.model_validate(project, from_attributes=True)
        new_project.user_id = current_user.id
        # First check if the project.name is unique
        # there might be flows with name like: "MyFlow", "MyFlow (1)", "MyFlow (2)"
        # so we need to check if the name is unique with `like` operator
        # if we find a flow with the same name, we add a number to the end of the name
        # based on the highest number found
        if (
            await session.exec(
                statement=select(Folder).where(Folder.name == new_project.name).where(Folder.user_id == current_user.id)
            )
        ).first():
            escaped_project_name = _escape_like(new_project.name)
            project_results = await session.exec(
                select(Folder).where(
                    Folder.name.like(f"{escaped_project_name}%", escape="\\"),  # type: ignore[attr-defined]
                    Folder.user_id == current_user.id,
                )
            )
            if project_results:
                project_names = [project.name for project in project_results]
                project_numbers = []
                for name in project_names:
                    if "(" not in name:
                        continue
                    try:
                        project_numbers.append(int(name.split("(")[-1].split(")")[0]))
                    except ValueError:
                        continue
                if project_numbers:
                    new_project.name = f"{new_project.name} ({max(project_numbers) + 1})"
                else:
                    new_project.name = f"{new_project.name} (1)"

        settings_service = get_settings_service()
        mcp_auth: dict = {"auth_type": "none"}

        if project.auth_settings:
            mcp_auth = project.auth_settings.copy()
            new_project.auth_settings = encrypt_auth_settings(mcp_auth)
        # If AUTO_LOGIN is false, automatically enable API key authentication
        elif not settings_service.auth_settings.AUTO_LOGIN:
            mcp_auth = {"auth_type": "apikey"}
            new_project.auth_settings = encrypt_auth_settings(mcp_auth)
            await logger.adebug(
                "Auto-enabled API key authentication for project %s (%s) due to AUTO_LOGIN=false",
                new_project.name,
                new_project.id,
            )

        session.add(new_project)
        await session.flush()
        await session.refresh(new_project)

        # Auto-register MCP server for this project with configured default auth
        if get_settings_service().settings.add_projects_to_mcp_servers:
            await register_mcp_servers_for_project(new_project, mcp_auth, current_user, session)

        if project.components_list:
            update_statement_components = (
                update(Flow)
                .where(Flow.id.in_(project.components_list), Flow.user_id == current_user.id)  # type: ignore[attr-defined]
                .values(folder_id=new_project.id)
            )
            await session.exec(update_statement_components)

        if project.flows_list:
            update_statement_flows = (
                update(Flow)
                .where(Flow.id.in_(project.flows_list), Flow.user_id == current_user.id)  # type: ignore[attr-defined]
                .values(folder_id=new_project.id)
            )
            await session.exec(update_statement_flows)

        # Convert to FolderRead while session is still active to avoid detached instance errors
        folder_read = FolderRead.model_validate(new_project, from_attributes=True)
    except HTTPException:
        # Re-raise HTTP exceptions (like 409 conflicts) without modification
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    return folder_read