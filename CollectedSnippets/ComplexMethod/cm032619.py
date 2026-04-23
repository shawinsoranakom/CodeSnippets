def test_getsse_auth_token_and_ownership_matrix_unit(monkeypatch):
    module = _load_canvas_module(monkeypatch)

    monkeypatch.setattr(module, "request", _DummyRequest(headers={"Authorization": "Bearer"}))
    res = module.getsse("canvas-1")
    assert res["message"] == "Authorization is not valid!"

    monkeypatch.setattr(module, "request", _DummyRequest(headers={"Authorization": "Bearer invalid"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [])
    res = module.getsse("canvas-1")
    assert "API key is invalid" in res["message"]

    monkeypatch.setattr(module, "request", _DummyRequest(headers={"Authorization": "Bearer ok"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [])
    res = module.getsse("canvas-1")
    assert res["code"] == module.RetCode.OPERATING_ERROR

    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [object()])
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _canvas_id: (False, None))
    res = module.getsse("canvas-1")
    assert res["message"] == "canvas not found."

    bad_owner = SimpleNamespace(user_id="tenant-2", to_dict=lambda: {"id": "canvas-1"})
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _canvas_id: (True, bad_owner))
    res = module.getsse("canvas-1")
    assert res["message"] == "canvas not found."

    good_owner = SimpleNamespace(user_id="tenant-1", to_dict=lambda: {"id": "canvas-1"})
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _canvas_id: (True, good_owner))
    res = module.getsse("canvas-1")
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["id"] == "canvas-1"