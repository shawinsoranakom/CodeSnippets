async def test_get_project_data():
    projects = await load_starter_projects()
    for _, project in projects:
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
        assert isinstance(project_gradient, str) or project_gradient is None
        assert isinstance(project_tags, list), f"Project {project_name} has no tags"
        assert isinstance(project_name, str), f"Project {project_name} has no name"
        assert isinstance(project_description, str), f"Project {project_name} has no description"
        assert isinstance(project_is_component, bool), f"Project {project_name} has no is_component"
        assert isinstance(updated_at_datetime, datetime), f"Project {project_name} has no updated_at_datetime"
        assert isinstance(project_data, dict), f"Project {project_name} has no data"
        assert isinstance(project_icon, str) or project_icon is None, f"Project {project_name} has no icon"
        assert isinstance(project_icon_bg_color, str) or project_icon_bg_color is None, (
            f"Project {project_name} has no icon_bg_color"
        )