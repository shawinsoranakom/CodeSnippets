def validate_flow_code(template_data: dict[str, Any], filename: str) -> list[str]:
    """Validate flow code using direct function call.

    Args:
        template_data: The template data to validate
        filename: Name of the template file for error reporting

    Returns:
        List of validation errors, empty if validation passes
    """
    errors = []

    try:
        # Extract code fields from template for validation
        data = template_data.get("data", template_data)

        for node in data.get("nodes", []):
            node_data = node.get("data", {})
            node_template = node_data.get("node", {}).get("template", {})

            # Look for code-related fields in the node template
            for field_data in node_template.values():
                if isinstance(field_data, dict) and field_data.get("type") == "code":
                    code_value = field_data.get("value", "")
                    if code_value and isinstance(code_value, str):
                        # Validate the code using direct function call
                        validation_result = validate_code(code_value)

                        # Check for import errors
                        if validation_result.get("imports", {}).get("errors"):
                            errors.extend(
                                [
                                    f"{filename}: Import error in node {node_data.get('id', 'unknown')}: {error}"
                                    for error in validation_result["imports"]["errors"]
                                ]
                            )

                        # Check for function errors
                        if validation_result.get("function", {}).get("errors"):
                            errors.extend(
                                [
                                    f"{filename}: Function error in node {node_data.get('id', 'unknown')}: {error}"
                                    for error in validation_result["function"]["errors"]
                                ]
                            )

    except (ValueError, TypeError, KeyError, AttributeError) as e:
        errors.append(f"{filename}: Code validation failed: {e!s}")

    return errors