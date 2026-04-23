async def create_or_update_starter_projects(all_types_dict: dict) -> None:
    """Create or update starter projects.

    Args:
        all_types_dict (dict): Dictionary containing all component types and their templates
    """
    if not get_settings_service().settings.create_starter_projects:
        # no-op for environments that don't want to create starter projects.
        # note that this doesn't check if the starter projects are already loaded in the db;
        # this is intended to be used to skip all startup project logic.
        return

    async with session_scope() as session:
        new_folder = await get_or_create_starter_folder(session)
        starter_projects = await load_starter_projects()

        if get_settings_service().settings.update_starter_projects:
            await logger.adebug("Updating starter projects")
            # 1. Delete all existing starter projects
            successfully_updated_projects = 0
            await delete_starter_projects(session, new_folder.id)
            # Profile pictures are now served directly from the package installation directory
            # No need to copy them to config_dir

            # 2. Update all starter projects with the latest component versions (this modifies the actual file data)
            for project_path, project in starter_projects:
                (
                    project_name,
                    project_description,
                    project_is_component,
                    updated_at_datetime,
                    project_data,
                    project_icon,
                    project_icon_bg_color,
                    project_gradient,
                    project_tags,
                ) = get_project_data(project)
                updated_project_data = update_projects_components_with_latest_component_versions(
                    project_data.copy(), all_types_dict
                )
                updated_project_data = update_edges_with_latest_component_versions(updated_project_data)
                if updated_project_data != project_data:
                    project_data = updated_project_data
                    await update_project_file(project_path, project, updated_project_data)

                try:
                    # Create the updated starter project
                    create_new_project(
                        session=session,
                        project_name=project_name,
                        project_description=project_description,
                        project_is_component=project_is_component,
                        updated_at_datetime=updated_at_datetime,
                        project_data=project_data,
                        project_icon=project_icon,
                        project_icon_bg_color=project_icon_bg_color,
                        project_gradient=project_gradient,
                        project_tags=project_tags,
                        new_folder_id=new_folder.id,
                    )
                except Exception:  # noqa: BLE001
                    await logger.aexception(f"Error while creating starter project {project_name}")

                successfully_updated_projects += 1
            await logger.adebug(f"Successfully updated {successfully_updated_projects} starter projects")
        else:
            # Even if we're not updating starter projects, we still need to create any that don't exist
            await logger.adebug("Creating new starter projects")
            successfully_created_projects = 0
            existing_flows = await get_all_flows_similar_to_project(session, new_folder.id)
            existing_flow_names = [existing_flow.name for existing_flow in existing_flows]
            for _, project in starter_projects:
                (
                    project_name,
                    project_description,
                    project_is_component,
                    updated_at_datetime,
                    project_data,
                    project_icon,
                    project_icon_bg_color,
                    project_gradient,
                    project_tags,
                ) = get_project_data(project)
                if project_name not in existing_flow_names:
                    try:
                        create_new_project(
                            session=session,
                            project_name=project_name,
                            project_description=project_description,
                            project_is_component=project_is_component,
                            updated_at_datetime=updated_at_datetime,
                            project_data=project_data,
                            project_icon=project_icon,
                            project_icon_bg_color=project_icon_bg_color,
                            project_gradient=project_gradient,
                            project_tags=project_tags,
                            new_folder_id=new_folder.id,
                        )
                    except Exception:  # noqa: BLE001
                        await logger.aexception(f"Error while creating starter project {project_name}")
                    successfully_created_projects += 1
                await logger.adebug(f"Successfully created {successfully_created_projects} starter projects")