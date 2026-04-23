def test_test_tool_route_matrix_unit(monkeypatch):
    module = _load_mcp_server_app(monkeypatch)

    _set_request_json(monkeypatch, module, {"mcp_id": "", "tool_name": "tool_a", "arguments": {"x": 1}})
    res = _run(module.test_tool.__wrapped__())
    assert "No MCP server ID provided" in res["message"]

    _set_request_json(monkeypatch, module, {"mcp_id": "id1", "tool_name": "", "arguments": {"x": 1}})
    res = _run(module.test_tool.__wrapped__())
    assert "Require provide tool name and arguments" in res["message"]

    _set_request_json(monkeypatch, module, {"mcp_id": "id1", "tool_name": "tool_a", "arguments": {}})
    res = _run(module.test_tool.__wrapped__())
    assert "Require provide tool name and arguments" in res["message"]

    _set_request_json(monkeypatch, module, {"mcp_id": "id1", "tool_name": "tool_a", "arguments": {"x": 1}})
    monkeypatch.setattr(module.MCPServerService, "get_by_id", lambda _mcp_id: (False, None))
    res = _run(module.test_tool.__wrapped__())
    assert "Cannot find MCP server id1 for user tenant_1" in res["message"]

    server_other = _DummyMCPServer(id="id1", name="srv", url="http://a", server_type="sse", tenant_id="other", variables={})
    monkeypatch.setattr(module.MCPServerService, "get_by_id", lambda _mcp_id: (True, server_other))
    res = _run(module.test_tool.__wrapped__())
    assert "Cannot find MCP server id1 for user tenant_1" in res["message"]

    server_ok = _DummyMCPServer(id="id1", name="srv", url="http://a", server_type="sse", tenant_id="tenant_1", variables={})
    monkeypatch.setattr(module.MCPServerService, "get_by_id", lambda _mcp_id: (True, server_ok))
    close_calls = []

    async def _thread_pool_exec_success(func, *args):
        if func is module.close_multiple_mcp_toolcall_sessions:
            close_calls.append(args[0])
            return None
        return func(*args)

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_exec_success)
    res = _run(module.test_tool.__wrapped__())
    assert res["code"] == 0
    assert res["data"] == "ok"
    assert close_calls and len(close_calls[-1]) == 1

    async def _thread_pool_exec_raise(func, *args):
        if func is module.close_multiple_mcp_toolcall_sessions:
            return None
        raise RuntimeError("tool call explode")

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_exec_raise)
    res = _run(module.test_tool.__wrapped__())
    assert res["code"] == 100
    assert "tool call explode" in res["message"]