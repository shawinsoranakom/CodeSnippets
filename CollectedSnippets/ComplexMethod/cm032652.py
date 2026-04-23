def test_import_multiple_mixed_results(monkeypatch):
    module = _load_mcp_server_app(monkeypatch)

    payload = {
        "mcpServers": {
            "missing_fields": {"type": "sse"},
            "": {"type": "sse", "url": "http://empty"},
            "dup": {"type": "sse", "url": "http://dup", "authorization_token": "dup-token"},
            "tool_err": {"type": "sse", "url": "http://err"},
            "insert_fail": {"type": "sse", "url": "http://fail"},
        },
        "timeout": "3",
    }
    _set_request_json(monkeypatch, module, payload)

    monkeypatch.setattr(module, "get_uuid", lambda: "uuid-import")

    def _get_by_name_and_tenant(name, tenant_id):
        if name == "dup" and not _get_by_name_and_tenant.first_dup_seen:
            _get_by_name_and_tenant.first_dup_seen = True
            return True, object()
        return False, None

    _get_by_name_and_tenant.first_dup_seen = False
    monkeypatch.setattr(module.MCPServerService, "get_by_name_and_tenant", _get_by_name_and_tenant)

    async def _thread_pool_exec(func, servers, _timeout):
        mcp_server = servers[0]
        if mcp_server.name == "tool_err":
            return None, "tool call failed"
        return {mcp_server.name: [{"name": "tool_a"}, {"invalid": True}]}, None

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_exec)

    def _insert(**kwargs):
        return kwargs["name"] != "insert_fail"

    monkeypatch.setattr(module.MCPServerService, "insert", _insert)

    res = _run(module.import_multiple.__wrapped__())
    assert res["code"] == 0

    results = {item["server"]: item for item in res["data"]["results"]}
    assert results["missing_fields"]["success"] is False
    assert "Missing required fields" in results["missing_fields"]["message"]
    assert results[""]["success"] is False
    assert "Invalid MCP name" in results[""]["message"]
    assert results["tool_err"]["success"] is False
    assert "tool call failed" in results["tool_err"]["message"]
    assert results["insert_fail"]["success"] is False
    assert "Failed to create MCP server" in results["insert_fail"]["message"]
    assert results["dup"]["success"] is True
    assert results["dup"]["new_name"] == "dup_0"
    assert "Renamed from 'dup' to 'dup_0' avoid duplication" == results["dup"]["message"]