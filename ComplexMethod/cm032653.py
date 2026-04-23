def test_list_tools_missing_ids_success_inner_error_outer_error_and_finally_cleanup(monkeypatch):
    module = _load_mcp_server_app(monkeypatch)

    _set_request_json(monkeypatch, module, {"mcp_ids": []})
    res = _run(module.list_tools.__wrapped__())
    assert "No MCP server IDs provided" in res["message"]

    server = _DummyMCPServer(
        id="id1",
        name="srv-tools",
        url="http://tools",
        server_type="sse",
        tenant_id="tenant_1",
        variables={"tools": {"tool_a": {"enabled": False}}},
    )

    _set_request_json(monkeypatch, module, {"mcp_ids": ["id1"], "timeout": "2.0"})
    monkeypatch.setattr(module.MCPServerService, "get_by_id", lambda _mcp_id: (True, server))

    close_calls = []

    async def _thread_pool_exec_success(func, *args):
        if func is module.close_multiple_mcp_toolcall_sessions:
            close_calls.append(args[0])
            return None
        return func(*args)

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_exec_success)
    res = _run(module.list_tools.__wrapped__())
    assert res["code"] == 0
    assert res["data"]["id1"][0]["name"] == "tool_a"
    assert res["data"]["id1"][0]["enabled"] is False
    assert res["data"]["id1"][1]["enabled"] is True
    assert close_calls and len(close_calls[-1]) == 1

    _set_request_json(monkeypatch, module, {"mcp_ids": ["id1"], "timeout": "2.0"})
    close_calls_inner = []

    async def _thread_pool_exec_inner_error(func, *args):
        if func is module.close_multiple_mcp_toolcall_sessions:
            close_calls_inner.append(args[0])
            return None
        raise RuntimeError("inner tools explode")

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_exec_inner_error)
    res = _run(module.list_tools.__wrapped__())
    assert res["code"] == 102
    assert "MCP list tools error" in res["message"]
    assert close_calls_inner and len(close_calls_inner[-1]) == 1

    _set_request_json(monkeypatch, module, {"mcp_ids": ["id1"], "timeout": "2.0"})
    close_calls_outer = []

    def _raise_get_by_id(_mcp_id):
        raise RuntimeError("outer explode")

    monkeypatch.setattr(module.MCPServerService, "get_by_id", _raise_get_by_id)

    async def _thread_pool_exec_outer(func, *args):
        if func is module.close_multiple_mcp_toolcall_sessions:
            close_calls_outer.append(args[0])
            return None
        return func(*args)

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_exec_outer)
    res = _run(module.list_tools.__wrapped__())
    assert res["code"] == 100
    assert "outer explode" in res["message"]
    assert close_calls_outer