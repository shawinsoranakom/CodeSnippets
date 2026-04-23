def list_templates(
    query: str | None = None,
    fields: list[str] | None = None,
    tags: list[str] | None = None,
    starter_projects_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Search and load template data with configurable field selection.

    Args:
        query: Optional search term to filter templates by name or description.
                     Case-insensitive substring matching.
        fields: List of fields to include in the results. If None, returns all available fields.
               Common fields: id, name, description, tags, is_component, last_tested_version,
               endpoint_name, data, icon, icon_bg_color, gradient, updated_at
        tags: Optional list of tags to filter templates. Returns templates that have ANY of these tags.
        starter_projects_path: Optional path to starter_projects directory.
                              If None, uses default location relative to initial_setup.

    Returns:
        List of dictionaries containing the selected fields for each matching template.

    Example:
        >>> # Get only id, name, and description
        >>> templates = list_templates(fields=["id", "name", "description"])

        >>> # Search for "agent" templates with specific fields
        >>> templates = list_templates(
        ...     search_query="agent",
        ...     fields=["id", "name", "description", "tags"]
        ... )

        >>> # Get templates by tag
        >>> templates = list_templates(
        ...     tags=["chatbots", "rag"],
        ...     fields=["name", "description"]
        ... )
    """
    # Get the starter_projects directory
    if starter_projects_path:
        starter_projects_dir = Path(starter_projects_path)
    else:
        # Navigate from agentic/utils back to initial_setup/starter_projects
        starter_projects_dir = Path(__file__).parent.parent.parent / "initial_setup" / "starter_projects"

    if not starter_projects_dir.exists():
        msg = f"Starter projects directory not found: {starter_projects_dir}"
        raise FileNotFoundError(msg)

    results = []

    # Iterate through all JSON files in the directory
    for template_file in starter_projects_dir.glob("*.json"):
        try:
            # Load the template
            with Path(template_file).open(encoding="utf-8") as f:
                template_data = json.load(f)

            # Apply search filter if provided
            if query:
                name = template_data.get("name", "").lower()
                description = template_data.get("description", "").lower()
                query_lower = query.lower()

                if query_lower not in name and query_lower not in description:
                    continue

            # Apply tag filter if provided
            if tags:
                template_tags = template_data.get("tags", [])
                if not template_tags:
                    continue
                # Check if any of the provided tags match
                if not any(tag in template_tags for tag in tags):
                    continue

            # Extract only the requested fields
            if fields:
                filtered_data = {field: template_data.get(field) for field in fields if field in template_data}
            else:
                # Return all fields if none specified
                filtered_data = template_data

            results.append(filtered_data)

        except (json.JSONDecodeError, orjson.JSONDecodeError) as e:
            # Log and skip invalid JSON files
            logger.warning(f"Failed to parse {template_file}: {e}")
            continue

    return results