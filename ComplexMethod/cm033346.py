async def import_multiple() -> Response:
    req = await get_request_json()
    servers = req.get("mcpServers", {})
    if not servers:
        return get_data_error_result(message="No MCP servers provided.")

    timeout = get_float(req, "timeout", 10)

    results = []
    try:
        for server_name, config in servers.items():
            if not all(key in config for key in {"type", "url"}):
                results.append({"server": server_name, "success": False, "message": "Missing required fields (type or url)"})
                continue

            if not server_name or len(server_name.encode("utf-8")) > 255:
                results.append({"server": server_name, "success": False, "message": f"Invalid MCP name or length is {len(server_name)} which is large than 255."})
                continue

            base_name = server_name
            new_name = base_name
            counter = 0

            while True:
                e, _ = MCPServerService.get_by_name_and_tenant(name=new_name, tenant_id=current_user.id)
                if not e:
                    break
                new_name = f"{base_name}_{counter}"
                counter += 1

            create_data = {
                "id": get_uuid(),
                "tenant_id": current_user.id,
                "name": new_name,
                "url": config["url"],
                "server_type": config["type"],
                "variables": {"authorization_token": config.get("authorization_token", "")},
            }

            headers = {"authorization_token": config["authorization_token"]} if "authorization_token" in config else {}
            variables = {k: v for k, v in config.items() if k not in {"type", "url", "headers"}}
            mcp_server = MCPServer(id=new_name, name=new_name, url=config["url"], server_type=config["type"], variables=variables, headers=headers)
            server_tools, err_message = await thread_pool_exec(get_mcp_tools, [mcp_server], timeout)
            if err_message:
                results.append({"server": base_name, "success": False, "message": err_message})
                continue

            tools = server_tools[new_name]
            tools = {tool["name"]: tool for tool in tools if isinstance(tool, dict) and "name" in tool}
            create_data["variables"]["tools"] = tools

            if MCPServerService.insert(**create_data):
                result = {"server": server_name, "success": True, "action": "created", "id": create_data["id"], "new_name": new_name}
                if new_name != base_name:
                    result["message"] = f"Renamed from '{base_name}' to '{new_name}' avoid duplication"
                results.append(result)
            else:
                results.append({"server": server_name, "success": False, "message": "Failed to create MCP server."})

        return get_json_result(data={"results": results})
    except Exception as e:
        return server_error_response(e)