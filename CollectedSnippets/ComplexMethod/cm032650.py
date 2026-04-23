def test_create_service_paths(monkeypatch):
    module = _load_mcp_server_app(monkeypatch)

    base_payload = {
        "name": "srv",
        "url": "http://server",
        "server_type": "sse",
        "headers": '{"Authorization": "x"}',
        "variables": '{"tools": {"old": 1}, "token": "abc"}',
        "timeout": "2.5",
    }

    monkeypatch.setattr(module, "get_uuid", lambda: "uuid-create")
    monkeypatch.setattr(module.MCPServerService, "get_by_name_and_tenant", lambda **_kwargs: (False, None))

    _set_request_json(monkeypatch, module, dict(base_payload))
    monkeypatch.setattr(module.TenantService, "get_by_id", lambda *_args, **_kwargs: (False, None))
    res = _run(module.create.__wrapped__())
    assert "Tenant not found" in res["message"]

    _set_request_json(monkeypatch, module, dict(base_payload))
    monkeypatch.setattr(module.TenantService, "get_by_id", lambda *_args, **_kwargs: (True, object()))

    async def _thread_pool_tools_error(_func, _servers, _timeout):
        return None, "tools error"

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_tools_error)
    res = _run(module.create.__wrapped__())
    assert res["code"] == "tools error"
    assert "Sorry! Data missing!" in res["message"]

    _set_request_json(monkeypatch, module, dict(base_payload))

    async def _thread_pool_ok(_func, servers, _timeout):
        return {servers[0].name: [{"name": "tool_a"}, {"invalid": True}]}, None

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_ok)
    monkeypatch.setattr(module.MCPServerService, "insert", lambda **_kwargs: False)
    res = _run(module.create.__wrapped__())
    assert res["code"] == "Failed to create MCP server."
    assert "Sorry! Data missing!" in res["message"]

    _set_request_json(monkeypatch, module, dict(base_payload))
    monkeypatch.setattr(module.MCPServerService, "insert", lambda **_kwargs: True)
    res = _run(module.create.__wrapped__())
    assert res["code"] == 0
    assert res["data"]["id"] == "uuid-create"
    assert res["data"]["tenant_id"] == "tenant_1"
    assert res["data"]["variables"]["tools"] == {"tool_a": {"name": "tool_a"}}

    _set_request_json(monkeypatch, module, dict(base_payload))

    async def _thread_pool_raises(_func, _servers, _timeout):
        raise RuntimeError("create explode")

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_raises)
    res = _run(module.create.__wrapped__())
    assert res["code"] == 100
    assert "create explode" in res["message"]