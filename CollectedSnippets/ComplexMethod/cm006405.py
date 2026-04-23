def get_template_by_id(
    template_id: str,
    fields: list[str] | None = None,
    starter_projects_path: str | Path | None = None,
) -> dict[str, Any] | None:
    """Get a specific template by its ID.

    Args:
        template_id: The UUID string of the template to retrieve.
        fields: Optional list of fields to include. If None, returns all fields.
        starter_projects_path: Optional path to starter_projects directory.

    Returns:
        Dictionary containing the template data with selected fields, or None if not found.

    Example:
        >>> template = get_template_by_id(
        ...     "0dbee653-41ae-4e51-af2e-55757fb24be3",
        ...     fields=["name", "description"]
        ... )
    """
    if starter_projects_path:
        starter_projects_dir = Path(starter_projects_path)
    else:
        starter_projects_dir = Path(__file__).parent.parent.parent / "initial_setup" / "starter_projects"

    for template_file in starter_projects_dir.glob("*.json"):
        try:
            with Path(template_file).open(encoding="utf-8") as f:
                template_data = json.load(f)

            if template_data.get("id") == template_id:
                if fields:
                    return {field: template_data.get(field) for field in fields if field in template_data}
                return template_data

        except (json.JSONDecodeError, orjson.JSONDecodeError):
            continue

    return None