async def create() -> Response:
    req = await get_request_json()

    server_type = req.get("server_type", "")
    if server_type not in VALID_MCP_SERVER_TYPES:
        return get_data_error_result(message="Unsupported MCP server type.")

    server_name = req.get("name", "")
    if not server_name or len(server_name.encode("utf-8")) > 255:
        return get_data_error_result(message=f"Invalid MCP name or length is {len(server_name)} which is large than 255.")

    e, _ = MCPServerService.get_by_name_and_tenant(name=server_name, tenant_id=current_user.id)
    if e:
        return get_data_error_result(message="Duplicated MCP server name.")

    url = req.get("url", "")
    if not url:
        return get_data_error_result(message="Invalid url.")

    headers = safe_json_parse(req.get("headers", {}))
    req["headers"] = headers
    variables = safe_json_parse(req.get("variables", {}))
    variables.pop("tools", None)

    timeout = get_float(req, "timeout", 10)

    try:
        req["id"] = get_uuid()
        req["tenant_id"] = current_user.id

        e, _ = TenantService.get_by_id(current_user.id)
        if not e:
            return get_data_error_result(message="Tenant not found.")

        mcp_server = MCPServer(id=server_name, name=server_name, url=url, server_type=server_type, variables=variables, headers=headers)
        server_tools, err_message = await thread_pool_exec(get_mcp_tools, [mcp_server], timeout)
        if err_message:
            return get_data_error_result(err_message)

        tools = server_tools[server_name]
        tools = {tool["name"]: tool for tool in tools if isinstance(tool, dict) and "name" in tool}
        variables["tools"] = tools
        req["variables"] = variables

        if not MCPServerService.insert(**req):
            return get_data_error_result("Failed to create MCP server.")

        return get_json_result(data=req)
    except Exception as e:
        return server_error_response(e)