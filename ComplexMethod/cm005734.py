def _clean_descriptions(spec: dict[str, Any]) -> None:
    """Convert newlines in operation descriptions to <br> for better ReDoc rendering."""
    paths = spec.get("paths") or {}
    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            description = operation.get("description")
            if isinstance(description, str) and description:
                operation["description"] = description.replace("\n", "<br>")