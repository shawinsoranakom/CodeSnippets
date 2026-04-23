async def discover_tools(
    request: DiscoverToolsRequest,
    user_id: Annotated[str, Security(get_user_id)],
) -> DiscoverToolsResponse:
    """
    Connect to an MCP server and return its available tools.

    If the user has a stored MCP credential for this server URL, it will be
    used automatically — no need to pass an explicit auth token.
    """
    # Validate URL to prevent SSRF — blocks loopback and private IP ranges.
    try:
        await validate_url_host(request.server_url)
    except ValueError as e:
        raise fastapi.HTTPException(status_code=400, detail=f"Invalid server URL: {e}")

    auth_token = request.auth_token

    # Auto-use stored MCP credential when no explicit token is provided.
    if not auth_token:
        best_cred = await auto_lookup_mcp_credential(
            user_id, normalize_mcp_url(request.server_url)
        )
        if best_cred:
            auth_token = best_cred.access_token.get_secret_value()

    client = MCPClient(request.server_url, auth_token=auth_token)

    try:
        init_result = await client.initialize()
        tools = await client.list_tools()
    except HTTPClientError as e:
        if e.status_code in (401, 403):
            raise fastapi.HTTPException(
                status_code=401,
                detail="This MCP server requires authentication. "
                "Please provide a valid auth token.",
            )
        raise fastapi.HTTPException(status_code=502, detail=str(e))
    except MCPClientError as e:
        raise fastapi.HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise fastapi.HTTPException(
            status_code=502,
            detail=f"Failed to connect to MCP server: {e}",
        )

    return DiscoverToolsResponse(
        tools=[
            MCPToolResponse(
                name=t.name,
                description=t.description,
                input_schema=t.input_schema,
            )
            for t in tools
        ],
        server_name=(
            init_result.get("serverInfo", {}).get("name")
            or server_host(request.server_url)
            or "MCP"
        ),
        protocol_version=init_result.get("protocolVersion"),
    )