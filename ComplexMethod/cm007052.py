def _get_tool_schema_description(tool) -> str:
    """Extract a brief description of the tool's expected parameters.

    Returns empty string if schema extraction fails (graceful degradation).
    """
    if not hasattr(tool, "args_schema") or not tool.args_schema:
        return ""

    schema = tool.args_schema
    if not hasattr(schema, "model_fields"):
        return ""

    try:
        fields = schema.model_fields
        params = []
        for name, field in fields.items():
            required = field.is_required() if hasattr(field, "is_required") else True
            req_str = "(required)" if required else "(optional)"
            params.append(f"{name} {req_str}")
        return f"Parameters: {', '.join(params)}" if params else ""
    except (AttributeError, TypeError) as e:
        logger.debug(f"Could not extract schema for tool {getattr(tool, 'name', 'unknown')}: {e}")
        return ""