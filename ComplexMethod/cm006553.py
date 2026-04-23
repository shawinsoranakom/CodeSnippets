def validate_template_structure(template_data: dict[str, Any], filename: str) -> list[str]:
    """Validate basic template structure.

    Args:
        template_data: The template data to validate
        filename: Name of the template file for error reporting

    Returns:
        List of error messages, empty if validation passes
    """
    errors = []

    # Handle wrapped format
    data = template_data.get("data", template_data)

    # Check required fields
    if "nodes" not in data:
        errors.append(f"{filename}: Missing 'nodes' field")
    elif not isinstance(data["nodes"], list):
        errors.append(f"{filename}: 'nodes' must be a list")

    if "edges" not in data:
        errors.append(f"{filename}: Missing 'edges' field")
    elif not isinstance(data["edges"], list):
        errors.append(f"{filename}: 'edges' must be a list")

    # Check nodes have required fields
    for i, node in enumerate(data.get("nodes", [])):
        if "id" not in node:
            errors.append(f"{filename}: Node {i} missing 'id'")
        if "data" not in node:
            errors.append(f"{filename}: Node {i} missing 'data'")

    return errors