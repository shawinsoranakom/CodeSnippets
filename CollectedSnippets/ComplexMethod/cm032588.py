def test_detail_branches(monkeypatch):
    module = _load_kb_module(monkeypatch)

    _set_request_args(monkeypatch, module, {"kb_id": "kb-1"})
    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: [])
    res = inspect.unwrap(module.detail)()
    assert res["code"] == module.RetCode.OPERATING_ERROR, res

    _set_request_args(monkeypatch, module, {"kb_id": "kb-1"})
    monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: [SimpleNamespace(id="kb-1")])
    monkeypatch.setattr(module.KnowledgebaseService, "get_detail", lambda _kb_id: None)
    res = inspect.unwrap(module.detail)()
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "Can't find this dataset" in res["message"], res

    finish_at = datetime(2025, 1, 1, 12, 30, 0)
    kb_detail = {
        "id": "kb-1",
        "parser_config": {"metadata": {"x": "y"}},
        "graphrag_task_finish_at": finish_at,
        "raptor_task_finish_at": finish_at,
        "mindmap_task_finish_at": finish_at,
    }
    monkeypatch.setattr(module.KnowledgebaseService, "get_detail", lambda _kb_id: deepcopy(kb_detail))
    monkeypatch.setattr(module.DocumentService, "get_total_size_by_kb_id", lambda **_kwargs: 1024)
    monkeypatch.setattr(module.Connector2KbService, "list_connectors", lambda _kb_id: ["conn-1"])
    monkeypatch.setattr(module, "turn2jsonschema", lambda metadata: {"type": "object", "properties": metadata})
    res = inspect.unwrap(module.detail)()
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"]["size"] == 1024, res
    assert res["data"]["connectors"] == ["conn-1"], res
    assert isinstance(res["data"]["parser_config"]["metadata"], dict), res
    assert res["data"]["graphrag_task_finish_at"] == "2025-01-01 12:30:00", res

    def _raise_tenants(**_kwargs):
        raise RuntimeError("detail boom")
    monkeypatch.setattr(module.UserTenantService, "query", _raise_tenants)
    res = inspect.unwrap(module.detail)()
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "detail boom" in res["message"], res