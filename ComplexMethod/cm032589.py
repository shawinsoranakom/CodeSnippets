def test_tags_and_meta_branches(monkeypatch):
    module = _load_kb_module(monkeypatch)

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: False)
    res = inspect.unwrap(module.list_tags)("kb-1")
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.UserTenantService, "get_tenants_by_user_id", lambda _uid: [{"tenant_id": "tenant-1"}, {"tenant_id": "tenant-2"}])
    monkeypatch.setattr(module.settings, "retriever", SimpleNamespace(all_tags=lambda tenant_id, kb_ids: [f"{tenant_id}:{kb_ids[0]}"]))
    res = inspect.unwrap(module.list_tags)("kb-1")
    assert res["code"] == module.RetCode.SUCCESS, res
    assert len(res["data"]) == 2, res

    _set_request_args(monkeypatch, module, {"kb_ids": "kb-1,kb-2"})
    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda kb_id, _uid: kb_id == "kb-1")
    res = inspect.unwrap(module.list_tags_from_kbs)()
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: True)
    res = inspect.unwrap(module.list_tags_from_kbs)()
    assert res["code"] == module.RetCode.SUCCESS, res
    assert isinstance(res["data"], list), res

    _set_request_json(monkeypatch, module, {"tags": ["a", "b"]})
    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: False)
    res = _run(inspect.unwrap(module.rm_tags)("kb-1"))
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, _DummyKB(tenant_id="tenant-1")))
    monkeypatch.setattr(module.settings, "docStoreConn", SimpleNamespace(update=lambda *_args, **_kwargs: True))
    monkeypatch.setattr(module.search, "index_name", lambda _tenant_id: "idx")
    res = _run(inspect.unwrap(module.rm_tags)("kb-1"))
    assert res["code"] == module.RetCode.SUCCESS, res

    _set_request_json(monkeypatch, module, {"from_tag": "a", "to_tag": "b"})
    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: False)
    res = _run(inspect.unwrap(module.rename_tags)("kb-1"))
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: True)
    res = _run(inspect.unwrap(module.rename_tags)("kb-1"))
    assert res["code"] == module.RetCode.SUCCESS, res

    _set_request_args(monkeypatch, module, {"kb_ids": "kb-1,kb-2"})
    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda kb_id, _uid: kb_id == "kb-1")
    res = inspect.unwrap(module.get_meta)()
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.DocMetadataService, "get_flatted_meta_by_kbs", lambda _kb_ids: {"source": ["a"]})
    res = inspect.unwrap(module.get_meta)()
    assert res["code"] == module.RetCode.SUCCESS, res
    assert "source" in res["data"], res

    _set_request_args(monkeypatch, module, {"kb_id": "kb-1"})
    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: False)
    res = inspect.unwrap(module.get_basic_info)()
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.DocumentService, "knowledgebase_basic_info", lambda _kb_id: {"finished": 1})
    res = inspect.unwrap(module.get_basic_info)()
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"]["finished"] == 1, res