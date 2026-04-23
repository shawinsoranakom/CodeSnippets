def test_update_route_branch_matrix_unit(monkeypatch):
    module = _load_dataset_module(monkeypatch)
    req_state = {"name": "new"}
    _patch_json_parser(monkeypatch, module, req_state)

    monkeypatch.setattr(module.KnowledgebaseService, "get_or_none", lambda **_kwargs: None)
    res = _run(inspect.unwrap(module.update)("tenant-1", "kb-1"))
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "lacks permission for dataset" in res["message"], res

    kb = _KB(kb_id="kb-1", name="old", chunk_num=0)

    def _get_or_none_duplicate(**kwargs):
        if kwargs.get("id"):
            return kb
        if kwargs.get("name"):
            return SimpleNamespace(id="dup")
        return None

    monkeypatch.setattr(module.KnowledgebaseService, "get_or_none", _get_or_none_duplicate)
    req_state.clear()
    req_state.update({"name": "new"})
    res = _run(inspect.unwrap(module.update)("tenant-1", "kb-1"))
    assert "already exists" in res["message"], res

    kb_chunked = _KB(kb_id="kb-1", name="old", chunk_num=2, embd_id="embd-1")
    monkeypatch.setattr(module.KnowledgebaseService, "get_or_none", lambda **kwargs: kb_chunked if kwargs.get("id") else None)
    req_state.clear()
    req_state.update({"embd_id": "embd-2"})
    res = _run(inspect.unwrap(module.update)("tenant-1", "kb-1"))
    assert "chunk_num" in res["message"], res

    kb_rank = _KB(kb_id="kb-1", name="old", pagerank=0)
    monkeypatch.setattr(module.KnowledgebaseService, "get_or_none", lambda **kwargs: kb_rank if kwargs.get("id") else None)
    req_state.clear()
    req_state.update({"pagerank": 3})
    os.environ["DOC_ENGINE"] = "infinity"
    res = _run(inspect.unwrap(module.update)("tenant-1", "kb-1"))
    assert "doc_engine" in res["message"], res
    os.environ.pop("DOC_ENGINE", None)

    update_calls = []
    monkeypatch.setattr(module.settings, "docStoreConn", SimpleNamespace(update=lambda *args, **_kwargs: update_calls.append(args)))
    monkeypatch.setattr(module.KnowledgebaseService, "update_by_id", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, _KB(kb_id="kb-1", pagerank=3)))

    req_state.clear()
    req_state.update({"pagerank": 3})
    res = _run(inspect.unwrap(module.update)("tenant-1", "kb-1"))
    assert res["code"] == module.RetCode.SUCCESS, res
    assert update_calls and update_calls[-1][0] == {"kb_id": "kb-1"}, update_calls

    update_calls.clear()
    monkeypatch.setattr(module.KnowledgebaseService, "get_or_none", lambda **kwargs: _KB(kb_id="kb-1", pagerank=3) if kwargs.get("id") else None)
    req_state.clear()
    req_state.update({"pagerank": 0})
    res = _run(inspect.unwrap(module.update)("tenant-1", "kb-1"))
    assert res["code"] == module.RetCode.SUCCESS, res
    assert update_calls and update_calls[-1][0] == {"exists": module.dataset_api_service.PAGERANK_FLD}, update_calls

    monkeypatch.setattr(module.KnowledgebaseService, "update_by_id", lambda *_args, **_kwargs: False)
    req_state.clear()
    req_state.update({"description": "changed"})
    res = _run(inspect.unwrap(module.update)("tenant-1", "kb-1"))
    assert "Update dataset error" in res["message"], res

    monkeypatch.setattr(module.KnowledgebaseService, "update_by_id", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (False, None))
    res = _run(inspect.unwrap(module.update)("tenant-1", "kb-1"))
    assert "Dataset updated failed" in res["message"], res

    monkeypatch.setattr(
        module.KnowledgebaseService,
        "get_or_none",
        lambda **_kwargs: (_ for _ in ()).throw(module.OperationalError("update down")),
    )
    res = _run(inspect.unwrap(module.update)("tenant-1", "kb-1"))
    assert res["message"] == "Database operation failed", res