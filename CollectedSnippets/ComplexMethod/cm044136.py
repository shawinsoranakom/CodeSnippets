def get_mcp_config(route: APIRoute, *, strict: bool = False) -> MCPConfigModel:
    """
    Read and validate per-route MCP config from openapi_extra.

    Args:
        route: The APIRoute to process.
        strict: If True, raise validation errors. If False, log warnings.

    Returns:
        A validated MCPConfigModel instance.
    """
    extra = route.openapi_extra or {}
    raw_config = extra.get("mcp_config") or extra.get("x-mcp") or {}

    if not isinstance(raw_config, dict):
        if strict:
            raise TypeError("mcp_config must be a dictionary.")
        raw_config = {}

    try:
        return validate_mcp_config(raw_config, strict=strict)
    except (ValidationError, TypeError, ValueError) as e:
        if strict:
            raise e from e
        return MCPConfigModel()