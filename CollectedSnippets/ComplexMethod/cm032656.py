def test_test_mcp_route_matrix_unit(monkeypatch):
    module = _load_mcp_server_app(monkeypatch)

    _set_request_json(monkeypatch, module, {"url": "", "server_type": "sse"})
    res = _run(module.test_mcp.__wrapped__())
    assert "Invalid MCP url" in res["message"]

    _set_request_json(monkeypatch, module, {"url": "http://a", "server_type": "invalid"})
    res = _run(module.test_mcp.__wrapped__())
    assert "Unsupported MCP server type" in res["message"]

    close_calls = []

    async def _thread_pool_exec_inner_error(func, *args):
        if func is module.close_multiple_mcp_toolcall_sessions:
            close_calls.append(args[0])
            return None
        if getattr(func, "__name__", "") == "get_tools":
            raise RuntimeError("get tools explode")
        return func(*args)

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_exec_inner_error)
    _set_request_json(monkeypatch, module, {"url": "http://a", "server_type": "sse"})
    res = _run(module.test_mcp.__wrapped__())
    assert res["code"] == 102
    assert "Test MCP error: get tools explode" in res["message"]
    assert close_calls and len(close_calls[-1]) == 1

    close_calls_success = []

    async def _thread_pool_exec_success(func, *args):
        if func is module.close_multiple_mcp_toolcall_sessions:
            close_calls_success.append(args[0])
            return None
        return func(*args)

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_exec_success)
    _set_request_json(monkeypatch, module, {"url": "http://a", "server_type": "sse"})
    res = _run(module.test_mcp.__wrapped__())
    assert res["code"] == 0
    assert res["data"][0]["name"] == "tool_a"
    assert all(tool["enabled"] is True for tool in res["data"])
    assert close_calls_success and len(close_calls_success[-1]) == 1

    def _raise_session(*_args, **_kwargs):
        raise RuntimeError("session explode")

    monkeypatch.setattr(module, "MCPToolCallSession", _raise_session)
    _set_request_json(monkeypatch, module, {"url": "http://a", "server_type": "sse"})
    res = _run(module.test_mcp.__wrapped__())
    assert res["code"] == 100
    assert "session explode" in res["message"]