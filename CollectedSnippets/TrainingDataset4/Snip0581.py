def type_to_readable(type_schema: dict[str, Any] | Any) -> str:
    """Convert JSON schema type to human-readable string."""
    if not isinstance(type_schema, dict):
        return str(type_schema) if type_schema else "Any"

    if "anyOf" in type_schema:
        # Union type - show options
        any_of = type_schema["anyOf"]
        if not isinstance(any_of, list):
            return "Any"
        options = []
        for opt in any_of:
            if isinstance(opt, dict) and opt.get("type") == "null":
                continue
            options.append(type_to_readable(opt))
        if not options:
            return "None"
        if len(options) == 1:
            return options[0]
        return " | ".join(options)

    if "allOf" in type_schema:
        all_of = type_schema["allOf"]
        if not isinstance(all_of, list) or not all_of:
            return "Any"
        return type_to_readable(all_of[0])

    schema_type = type_schema.get("type")

    if schema_type == "array":
        items = type_schema.get("items", {})
        item_type = type_to_readable(items)
        return f"List[{item_type}]"

    if schema_type == "object":
        if "additionalProperties" in type_schema:
            additional_props = type_schema["additionalProperties"]
            # additionalProperties: true means any value type is allowed
            if additional_props is True:
                return "Dict[str, Any]"
            value_type = type_to_readable(additional_props)
            return f"Dict[str, {value_type}]"
        # Check if it's a specific model
        title = type_schema.get("title", "Object")
        return title

    if schema_type == "string":
        if "enum" in type_schema:
            return " | ".join(f'"{v}"' for v in type_schema["enum"])
        if "format" in type_schema:
            return f"str ({type_schema['format']})"
        return "str"

    if schema_type == "integer":
        return "int"

    if schema_type == "number":
        return "float"

    if schema_type == "boolean":
        return "bool"

    if schema_type == "null":
        return "None"

    # Fallback
    return type_schema.get("title", schema_type or "Any")
