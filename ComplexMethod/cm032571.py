def test_create_route_matrix_unit(monkeypatch):
    module = _load_search_api(monkeypatch)

    _set_request_json(monkeypatch, module, {"name": 1})
    res = _run(module.create())
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "must be string" in res["message"]

    _set_request_json(monkeypatch, module, {"name": "   "})
    res = _run(module.create())
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "empty" in res["message"].lower()

    _set_request_json(monkeypatch, module, {"name": "a" * 256})
    res = _run(module.create())
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "255" in res["message"]

    _set_request_json(monkeypatch, module, {"name": "create-auth-fail"})
    monkeypatch.setattr(module.TenantService, "get_by_id", lambda _tenant_id: (False, None))
    res = _run(module.create())
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "authorized identity" in res["message"].lower()

    monkeypatch.setattr(module.TenantService, "get_by_id", lambda _tenant_id: (True, SimpleNamespace(id=_tenant_id)))
    monkeypatch.setattr(module, "duplicate_name", lambda _checker, **kwargs: kwargs["name"] + "_dedup")
    _set_request_json(monkeypatch, module, {"name": "create-fail", "description": "d"})
    monkeypatch.setattr(module.SearchService, "save", lambda **_kwargs: False)
    res = _run(module.create())
    assert res["code"] == module.RetCode.DATA_ERROR

    _set_request_json(monkeypatch, module, {"name": "create-ok", "description": "d"})
    monkeypatch.setattr(module.SearchService, "save", lambda **_kwargs: True)
    res = _run(module.create())
    assert res["code"] == 0
    assert res["data"]["search_id"] == "search-uuid-1"

    def _raise_save(**_kwargs):
        raise RuntimeError("save boom")

    monkeypatch.setattr(module.SearchService, "save", _raise_save)
    _set_request_json(monkeypatch, module, {"name": "create-exception", "description": "d"})
    res = _run(module.create())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "save boom" in res["message"]