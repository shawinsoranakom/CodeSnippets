def test_delete_route_error_summary_matrix_unit(monkeypatch):
    module = _load_dataset_module(monkeypatch)
    req_state = {"ids": ["kb-1"]}
    _patch_json_parser(monkeypatch, module, req_state)

    kb = _KB(kb_id="kb-1", name="kb-1", tenant_id="tenant-1")
    monkeypatch.setattr(module.KnowledgebaseService, "get_or_none", lambda **_kwargs: kb)
    monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [SimpleNamespace(id="doc-1")])
    monkeypatch.setattr(module.DocumentService, "remove_document", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(module.settings, "docStoreConn", SimpleNamespace(delete_idx=lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("drop failed"))))
    monkeypatch.setattr(module.KnowledgebaseService, "delete_by_id", lambda _kb_id: False)
    res = _run(inspect.unwrap(module.delete)("tenant-1"))
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "Successfully deleted 0 datasets" in res["message"], res

    monkeypatch.setattr(module.settings, "docStoreConn", SimpleNamespace(delete_idx=lambda *_args, **_kwargs: None))
    monkeypatch.setattr(module.KnowledgebaseService, "delete_by_id", lambda _kb_id: True)
    res = _run(inspect.unwrap(module.delete)("tenant-1"))
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"]["success_count"] == 1, res
    assert res["data"]["errors"], res

    req_state["ids"] = None
    res = _run(inspect.unwrap(module.delete)("tenant-1"))
    assert res["code"] == module.RetCode.SUCCESS, res