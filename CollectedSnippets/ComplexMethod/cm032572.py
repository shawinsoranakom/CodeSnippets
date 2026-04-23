def test_update_and_detail_route_matrix_unit(monkeypatch):
    module = _load_search_api(monkeypatch)

    # update: name not string
    _set_request_json(monkeypatch, module, {"name": 1, "search_config": {}})
    res = _run(module.update(search_id="s1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "must be string" in res["message"]

    # update: empty name
    _set_request_json(monkeypatch, module, {"name": "   ", "search_config": {}})
    res = _run(module.update(search_id="s1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "empty" in res["message"].lower()

    # update: name too long
    _set_request_json(monkeypatch, module, {"name": "a" * 256, "search_config": {}})
    res = _run(module.update(search_id="s1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "large than" in res["message"]

    # update: tenant not found
    _set_request_json(monkeypatch, module, {"name": "ok", "search_config": {}})
    monkeypatch.setattr(module.TenantService, "get_by_id", lambda _tenant_id: (False, None))
    res = _run(module.update(search_id="s1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "authorized identity" in res["message"].lower()

    # update: no access
    monkeypatch.setattr(module.TenantService, "get_by_id", lambda _tenant_id: (True, SimpleNamespace(id=_tenant_id)))
    monkeypatch.setattr(module.SearchService, "accessible4deletion", lambda _search_id, _user_id: False)
    _set_request_json(monkeypatch, module, {"name": "ok", "search_config": {}})
    res = _run(module.update(search_id="s1"))
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR
    assert "authorization" in res["message"].lower()

    # update: search not found (query returns [None])
    monkeypatch.setattr(module.SearchService, "accessible4deletion", lambda _search_id, _user_id: True)
    monkeypatch.setattr(module.SearchService, "query", lambda **_kwargs: [None])
    _set_request_json(monkeypatch, module, {"name": "ok", "search_config": {}})
    res = _run(module.update(search_id="s1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "cannot find search" in res["message"].lower()

    existing = _SearchRecord(search_id="s1", name="old-name", search_config={"existing": 1})

    def _query_duplicate(**kwargs):
        if "id" in kwargs:
            return [existing]
        if "name" in kwargs:
            return [SimpleNamespace(id="dup")]
        return []

    # update: duplicate name
    monkeypatch.setattr(module.SearchService, "query", _query_duplicate)
    _set_request_json(monkeypatch, module, {"name": "new-name", "search_config": {}})
    res = _run(module.update(search_id="s1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "duplicated" in res["message"].lower()

    # update: search_config not a dict
    monkeypatch.setattr(module.SearchService, "query", lambda **_kwargs: [existing])
    _set_request_json(monkeypatch, module, {"name": "old-name", "search_config": []})
    res = _run(module.update(search_id="s1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "json object" in res["message"].lower()

    # update: update_by_id fails, verifies config merge and field exclusion
    captured = {}

    def _update_fail(search_id, req):
        captured["search_id"] = search_id
        captured["req"] = dict(req)
        return False

    monkeypatch.setattr(module.SearchService, "update_by_id", _update_fail)
    _set_request_json(monkeypatch, module, {"name": "old-name", "search_config": {"top_k": 3}})
    res = _run(module.update(search_id="s1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "failed to update" in res["message"].lower()
    assert captured["search_id"] == "s1"
    assert captured["req"]["search_config"] == {"existing": 1, "top_k": 3}

    # update: get_by_id fails after successful update
    monkeypatch.setattr(module.SearchService, "update_by_id", lambda _search_id, _req: True)
    monkeypatch.setattr(module.SearchService, "get_by_id", lambda _search_id: (False, None))
    res = _run(module.update(search_id="s1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "failed to fetch" in res["message"].lower()

    # update: success
    monkeypatch.setattr(
        module.SearchService,
        "get_by_id",
        lambda _search_id: (True, _SearchRecord(search_id=_search_id, name="old-name", search_config={"existing": 1, "top_k": 3})),
    )
    res = _run(module.update(search_id="s1"))
    assert res["code"] == 0
    assert res["data"]["id"] == "s1"

    # update: exception
    def _raise_query(**_kwargs):
        raise RuntimeError("update boom")

    monkeypatch.setattr(module.SearchService, "query", _raise_query)
    _set_request_json(monkeypatch, module, {"name": "old-name", "search_config": {"top_k": 3}})
    res = _run(module.update(search_id="s1"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "update boom" in res["message"]

    # detail: no permission
    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-a")])
    monkeypatch.setattr(module.SearchService, "query", lambda **_kwargs: [])
    res = module.detail(search_id="s1")
    assert res["code"] == module.RetCode.OPERATING_ERROR
    assert "permission" in res["message"].lower()

    # detail: search not found
    monkeypatch.setattr(module.SearchService, "query", lambda **_kwargs: [SimpleNamespace(id="s1")])
    monkeypatch.setattr(module.SearchService, "get_detail", lambda _search_id: None)
    res = module.detail(search_id="s1")
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "can't find" in res["message"].lower()

    # detail: success
    monkeypatch.setattr(module.SearchService, "get_detail", lambda _search_id: {"id": _search_id, "name": "detail-name"})
    res = module.detail(search_id="s1")
    assert res["code"] == 0
    assert res["data"]["id"] == "s1"

    # detail: exception
    def _raise_detail(_search_id):
        raise RuntimeError("detail boom")

    monkeypatch.setattr(module.SearchService, "get_detail", _raise_detail)
    res = module.detail(search_id="s1")
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "detail boom" in res["message"]