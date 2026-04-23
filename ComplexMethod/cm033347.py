async def list_tools() -> Response:
    req = await get_request_json()
    mcp_ids = req.get("mcp_ids", [])
    if not mcp_ids:
        return get_data_error_result(message="No MCP server IDs provided.")

    timeout = get_float(req, "timeout", 10)

    results = {}
    tool_call_sessions = []
    try:
        for mcp_id in mcp_ids:
            e, mcp_server = MCPServerService.get_by_id(mcp_id)

            if e and mcp_server.tenant_id == current_user.id:
                server_key = mcp_server.id

                cached_tools = mcp_server.variables.get("tools", {})

                tool_call_session = MCPToolCallSession(mcp_server, mcp_server.variables)
                tool_call_sessions.append(tool_call_session)

                try:
                    tools = await thread_pool_exec(tool_call_session.get_tools, timeout)
                except Exception as e:
                    return get_data_error_result(message=f"MCP list tools error: {e}")

                results[server_key] = []
                for tool in tools:
                    tool_dict = tool.model_dump()
                    cached_tool = cached_tools.get(tool_dict["name"], {})

                    tool_dict["enabled"] = cached_tool.get("enabled", True)
                    results[server_key].append(tool_dict)

        return get_json_result(data=results)
    except Exception as e:
        return server_error_response(e)
    finally:
        # PERF: blocking call to close sessions — consider moving to background thread or task queue
        await thread_pool_exec(close_multiple_mcp_toolcall_sessions, tool_call_sessions)