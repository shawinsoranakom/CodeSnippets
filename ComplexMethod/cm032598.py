def test_agents_crud_unit_branches(monkeypatch):
    module = _load_agents_app(monkeypatch)

    monkeypatch.setattr(
        module,
        "request",
        SimpleNamespace(args={"id": "missing", "title": "missing", "desc": "false", "page": "1", "page_size": "10"}),
    )
    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [])
    res = module.list_agents.__wrapped__("tenant-1")
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "doesn't exist" in res["message"]

    captured = {}

    def fake_get_list(_tenant_id, _page, _page_size, _orderby, desc, *_rest):
        captured["desc"] = desc
        return [{"id": "agent-1"}]

    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [{"id": "agent-1"}])
    monkeypatch.setattr(module.UserCanvasService, "get_list", fake_get_list)
    monkeypatch.setattr(module, "request", SimpleNamespace(args={"desc": "true"}))
    res = module.list_agents.__wrapped__("tenant-1")
    assert res["code"] == module.RetCode.SUCCESS
    assert captured["desc"] is True

    async def req_no_dsl():
        return {"title": "agent-a"}

    monkeypatch.setattr(module, "get_request_json", req_no_dsl)
    res = _run(module.create_agent.__wrapped__("tenant-1"))
    assert res["code"] == module.RetCode.ARGUMENT_ERROR
    assert "No DSL data in request" in res["message"]

    async def req_no_title():
        return {"dsl": {"components": {}}}

    monkeypatch.setattr(module, "get_request_json", req_no_title)
    res = _run(module.create_agent.__wrapped__("tenant-1"))
    assert res["code"] == module.RetCode.ARGUMENT_ERROR
    assert "No title in request" in res["message"]

    async def req_dup():
        return {"dsl": {"components": {}}, "title": "agent-dup"}

    monkeypatch.setattr(module, "get_request_json", req_dup)
    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [object()])
    res = _run(module.create_agent.__wrapped__("tenant-1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "already exists" in res["message"]

    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [])
    monkeypatch.setattr(module, "get_uuid", lambda: "agent-created")
    monkeypatch.setattr(module.UserCanvasService, "save", lambda **_kwargs: False)
    res = _run(module.create_agent.__wrapped__("tenant-1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "Fail to create agent" in res["message"]

    async def req_update():
        return {"dsl": {"nodes": []}, "title": "  webhook-agent  ", "unused": None}

    monkeypatch.setattr(module, "get_request_json", req_update)
    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: False)
    res = _run(module.update_agent.__wrapped__("tenant-1", "agent-1"))
    assert res["code"] == module.RetCode.OPERATING_ERROR

    calls = {"update": 0, "save_or_replace_latest": 0}
    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: True)
    monkeypatch.setattr(
        module.UserCanvasService,
        "update_by_id",
        lambda *_args, **_kwargs: calls.__setitem__("update", calls["update"] + 1),
    )
    monkeypatch.setattr(
        module.UserCanvasVersionService,
        "save_or_replace_latest",
        lambda *_args, **_kwargs: calls.__setitem__("save_or_replace_latest", calls["save_or_replace_latest"] + 1),
    )
    res = _run(module.update_agent.__wrapped__("tenant-1", "agent-1"))
    assert res["code"] == module.RetCode.SUCCESS
    assert calls == {"update": 1, "save_or_replace_latest": 1}

    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: False)
    res = module.delete_agent.__wrapped__("tenant-1", "agent-1")
    assert res["code"] == module.RetCode.OPERATING_ERROR