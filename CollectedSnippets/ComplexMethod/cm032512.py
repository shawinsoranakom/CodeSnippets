def test_searchbots_detail_share_embedded_matrix_unit(monkeypatch):
    module = _load_session_module(monkeypatch)
    handler = inspect.unwrap(module.detail_share_embedded)

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer"}, args={"search_id": "s-1"}))
    res = _run(handler())
    assert res["message"] == "Authorization is not valid!"

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer bad"}, args={"search_id": "s-1"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [])
    res = _run(handler())
    assert "API key is invalid" in res["message"]

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer ok"}, args={"search_id": "s-1"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="")])
    res = _run(handler())
    assert res["message"] == "permission denined."

    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-a")])
    monkeypatch.setattr(module.SearchService, "query", lambda **_kwargs: [])
    res = _run(handler())
    assert res["code"] == module.RetCode.OPERATING_ERROR
    assert "Has no permission for this operation." in res["message"]

    monkeypatch.setattr(module.SearchService, "query", lambda **_kwargs: [SimpleNamespace(id="s-1")])
    monkeypatch.setattr(module.SearchService, "get_detail", lambda _sid: None)
    res = _run(handler())
    assert res["message"] == "Can't find this Search App!"

    monkeypatch.setattr(module.SearchService, "get_detail", lambda _sid: {"id": "s-1", "name": "search-app"})
    res = _run(handler())
    assert res["code"] == 0
    assert res["data"]["id"] == "s-1"