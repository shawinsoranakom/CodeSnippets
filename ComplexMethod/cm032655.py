def test_cache_tool_route_matrix_unit(monkeypatch):
    module = _load_mcp_server_app(monkeypatch)

    _set_request_json(monkeypatch, module, {"mcp_id": "", "tools": [{"name": "tool_a"}]})
    res = _run(module.cache_tool.__wrapped__())
    assert "No MCP server ID provided" in res["message"]

    _set_request_json(monkeypatch, module, {"mcp_id": "id1", "tools": [{"name": "tool_a"}]})
    monkeypatch.setattr(module.MCPServerService, "get_by_id", lambda _mcp_id: (False, None))
    res = _run(module.cache_tool.__wrapped__())
    assert "Cannot find MCP server id1 for user tenant_1" in res["message"]

    server_other = _DummyMCPServer(id="id1", name="srv", url="http://a", server_type="sse", tenant_id="other", variables={})
    monkeypatch.setattr(module.MCPServerService, "get_by_id", lambda _mcp_id: (True, server_other))
    res = _run(module.cache_tool.__wrapped__())
    assert "Cannot find MCP server id1 for user tenant_1" in res["message"]

    server_fail = _DummyMCPServer(id="id1", name="srv", url="http://a", server_type="sse", tenant_id="tenant_1", variables={})
    monkeypatch.setattr(module.MCPServerService, "get_by_id", lambda _mcp_id: (True, server_fail))
    monkeypatch.setattr(module.MCPServerService, "filter_update", lambda *_args, **_kwargs: False)
    res = _run(module.cache_tool.__wrapped__())
    assert "Failed to updated MCP server" in res["message"]

    server_ok = _DummyMCPServer(
        id="id1",
        name="srv",
        url="http://a",
        server_type="sse",
        tenant_id="tenant_1",
        variables={"tools": {"old_tool": {"name": "old_tool"}}},
    )
    monkeypatch.setattr(module.MCPServerService, "get_by_id", lambda _mcp_id: (True, server_ok))
    monkeypatch.setattr(module.MCPServerService, "filter_update", lambda *_args, **_kwargs: True)
    _set_request_json(
        monkeypatch,
        module,
        {
            "mcp_id": "id1",
            "tools": [{"name": "tool_a", "enabled": True}, {"bad": 1}, "x", {"name": "tool_b", "enabled": False}],
        },
    )
    res = _run(module.cache_tool.__wrapped__())
    assert res["code"] == 0
    assert sorted(res["data"].keys()) == ["tool_a", "tool_b"]
    assert server_ok.variables["tools"]["tool_b"]["enabled"] is False