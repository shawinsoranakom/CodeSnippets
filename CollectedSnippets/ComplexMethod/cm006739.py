def _convert_pydantic_type_to_json_schema_type(param_info: dict) -> dict:
    """Convert Pydantic parameter info to OpenAI function calling JSON schema format.

    SPARC expects tools to be in OpenAI's function calling format, which uses
    JSON Schema for parameter specifications.

    Args:
        param_info: Parameter info from LangChain tool.args

    Returns:
        Dict with 'type' and optionally other JSON schema properties compatible
        with OpenAI function calling format
    """
    # Handle simple types first
    if "type" in param_info:
        schema_type = param_info["type"]

        # Direct type mappings
        if schema_type in ("string", "number", "integer", "boolean", "null", "object"):
            return {
                "type": schema_type,
                "description": param_info.get("description", ""),
            }

        # Array type
        if schema_type == "array":
            result = {"type": "array", "description": param_info.get("description", "")}
            # Add items schema if available
            if "items" in param_info:
                items_schema = _convert_pydantic_type_to_json_schema_type(param_info["items"])
                result["items"] = items_schema
            return result

    # Handle complex types with anyOf (unions like list[str] | None)
    if "anyOf" in param_info:
        # Find the most specific non-null type
        for variant in param_info["anyOf"]:
            if variant.get("type") == "null":
                continue  # Skip null variants

            # Process the non-null variant
            converted = _convert_pydantic_type_to_json_schema_type(variant)
            converted["description"] = param_info.get("description", "")

            # If it has a default value, it's optional
            if "default" in param_info:
                converted["default"] = param_info["default"]

            return converted

    # Handle oneOf (similar to anyOf)
    if "oneOf" in param_info:
        # Take the first non-null option
        for variant in param_info["oneOf"]:
            if variant.get("type") != "null":
                converted = _convert_pydantic_type_to_json_schema_type(variant)
                converted["description"] = param_info.get("description", "")
                return converted

    # Handle allOf (intersection types)
    if param_info.get("allOf"):
        # For now, take the first schema
        converted = _convert_pydantic_type_to_json_schema_type(param_info["allOf"][0])
        converted["description"] = param_info.get("description", "")
        return converted

    # Fallback: try to infer from title or default to string
    logger.debug(f"Could not determine type for param_info: {param_info}")
    return {
        "type": "string",  # Safe fallback
        "description": param_info.get("description", ""),
    }