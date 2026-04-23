def test_create_route_error_matrix_unit(monkeypatch):
    module = _load_dataset_module(monkeypatch)
    req_state = {"name": "kb"}
    _patch_json_parser(monkeypatch, module, req_state)

    monkeypatch.setattr(module.KnowledgebaseService, "create_with_name", lambda **_kwargs: (False, {"code": 777, "message": "early"}))
    res = _run(inspect.unwrap(module.create)("tenant-1"))
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert res["message"] == {"code": 777, "message": "early"}, res

    monkeypatch.setattr(module.KnowledgebaseService, "create_with_name", lambda **_kwargs: (True, {"id": "kb-1"}))
    monkeypatch.setattr(module.TenantService, "get_by_id", lambda _tenant_id: (False, None))
    res = _run(inspect.unwrap(module.create)("tenant-1"))
    assert res["message"] == "Tenant not found", res

    monkeypatch.setattr(module.TenantService, "get_by_id", lambda _tenant_id: (True, SimpleNamespace(embd_id="embd-1")))
    monkeypatch.setattr(module.KnowledgebaseService, "save", lambda **_kwargs: False)
    res = _run(inspect.unwrap(module.create)("tenant-1"))
    assert res["code"] == module.RetCode.DATA_ERROR, res

    monkeypatch.setattr(module.KnowledgebaseService, "save", lambda **_kwargs: True)
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (False, None))
    res = _run(inspect.unwrap(module.create)("tenant-1"))
    assert "Dataset created failed" in res["message"], res

    monkeypatch.setattr(module.KnowledgebaseService, "save", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("save boom")))
    res = _run(inspect.unwrap(module.create)("tenant-1"))
    assert res["message"] == "Internal server error", res