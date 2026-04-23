def test_update_service_paths(monkeypatch):
    module = _load_mcp_server_app(monkeypatch)

    existing = _DummyMCPServer(
        id="mcp-1",
        name="srv",
        url="http://server",
        server_type="sse",
        tenant_id="tenant_1",
        variables={"tools": {"old": {"enabled": True}}, "token": "abc"},
        headers={"Authorization": "old"},
    )
    updated = _DummyMCPServer(
        id="mcp-1",
        name="srv-new",
        url="http://server-new",
        server_type="sse",
        tenant_id="tenant_1",
        variables={"tools": {"tool_a": {"name": "tool_a"}}},
        headers={"Authorization": "new"},
    )

    base_payload = {
        "mcp_id": "mcp-1",
        "name": "srv-new",
        "url": "http://server-new",
        "server_type": "sse",
        "headers": '{"Authorization": "new"}',
        "variables": '{"tools": {"ignore": 1}, "token": "new"}',
        "timeout": "3.0",
    }

    _set_request_json(monkeypatch, module, dict(base_payload))
    monkeypatch.setattr(module.MCPServerService, "get_by_id", lambda _mcp_id: (True, existing))

    async def _thread_pool_tools_error(_func, _servers, _timeout):
        return None, "update tools error"

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_tools_error)
    res = _run(module.update.__wrapped__())
    assert res["code"] == "update tools error"
    assert "Sorry! Data missing!" in res["message"]

    _set_request_json(monkeypatch, module, dict(base_payload))

    async def _thread_pool_ok(_func, servers, _timeout):
        return {servers[0].name: [{"name": "tool_a"}, {"bad": True}]}, None

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_ok)
    monkeypatch.setattr(module.MCPServerService, "filter_update", lambda *_args, **_kwargs: False)
    res = _run(module.update.__wrapped__())
    assert "Failed to updated MCP server" in res["message"]

    _set_request_json(monkeypatch, module, dict(base_payload))
    monkeypatch.setattr(module.MCPServerService, "filter_update", lambda *_args, **_kwargs: True)

    def _get_by_id_fetch_fail(_mcp_id):
        if _get_by_id_fetch_fail.calls == 0:
            _get_by_id_fetch_fail.calls += 1
            return True, existing
        return False, None

    _get_by_id_fetch_fail.calls = 0
    monkeypatch.setattr(module.MCPServerService, "get_by_id", _get_by_id_fetch_fail)
    res = _run(module.update.__wrapped__())
    assert "Failed to fetch updated MCP server" in res["message"]

    _set_request_json(monkeypatch, module, dict(base_payload))

    def _get_by_id_success(_mcp_id):
        if _get_by_id_success.calls == 0:
            _get_by_id_success.calls += 1
            return True, existing
        return True, updated

    _get_by_id_success.calls = 0
    monkeypatch.setattr(module.MCPServerService, "get_by_id", _get_by_id_success)
    res = _run(module.update.__wrapped__())
    assert res["code"] == 0
    assert res["data"]["id"] == "mcp-1"

    _set_request_json(monkeypatch, module, dict(base_payload))
    monkeypatch.setattr(module.MCPServerService, "get_by_id", lambda _mcp_id: (True, existing))

    async def _thread_pool_raises(_func, _servers, _timeout):
        raise RuntimeError("update explode")

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_raises)
    res = _run(module.update.__wrapped__())
    assert res["code"] == 100
    assert "update explode" in res["message"]