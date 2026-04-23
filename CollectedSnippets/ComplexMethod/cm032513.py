def test_searchbots_mindmap_embedded_matrix_unit(monkeypatch):
    module = _load_session_module(monkeypatch)
    handler = inspect.unwrap(module.mindmap)

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer"}))
    res = _run(handler())
    assert res["message"] == "Authorization is not valid!"

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer bad"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [])
    res = _run(handler())
    assert "API key is invalid" in res["message"]

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer ok"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"question": "q", "kb_ids": ["kb-1"]}))

    captured = {}

    async def _gen_ok(question, kb_ids, tenant_id, search_config):
        captured["params"] = (question, kb_ids, tenant_id, search_config)
        return {"nodes": [question]}

    monkeypatch.setattr(module, "gen_mindmap", _gen_ok)
    res = _run(handler())
    assert res["code"] == 0
    assert res["data"] == {"nodes": ["q"]}
    assert captured["params"] == ("q", ["kb-1"], "tenant-1", {})

    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"question": "q2", "kb_ids": ["kb-1"], "search_id": "search-1"}),
    )
    monkeypatch.setattr(module.SearchService, "get_detail", lambda _sid: {"search_config": {"mode": "graph"}})
    res = _run(handler())
    assert res["code"] == 0
    assert captured["params"] == ("q2", ["kb-1"], "tenant-1", {"mode": "graph"})

    async def _gen_error(*_args, **_kwargs):
        return {"error": "mindmap boom"}

    monkeypatch.setattr(module, "gen_mindmap", _gen_error)
    res = _run(handler())
    assert "mindmap boom" in res["message"]