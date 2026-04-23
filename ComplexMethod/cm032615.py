def test_rm_chunk_delete_exception_partial_compensation_and_cleanup_unit(monkeypatch):
    module = _load_chunk_module(monkeypatch)

    monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (False, None))
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "chunk_ids": ["c1"]})
    res = _run(module.rm())
    assert res["message"] == "Document not found!", res

    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "chunk_ids": []})
    monkeypatch.setattr(
        module.DocumentService,
        "get_by_id",
        lambda _doc_id: (_ for _ in ()).throw(AssertionError("get_by_id must not run for empty delete payload")),
    )
    monkeypatch.setattr(
        module.settings.docStoreConn,
        "delete",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("delete must not run for empty delete payload")),
    )
    res = _run(module.rm())
    assert res["code"] == 0, res

    monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (True, _DummyDoc()))

    def _raise_delete(*_args, **_kwargs):
        raise RuntimeError("delete boom")

    monkeypatch.setattr(module.settings.docStoreConn, "delete", _raise_delete)
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "chunk_ids": ["c1"]})
    res = _run(module.rm())
    assert res["message"] == "Chunk deleting failure", res

    def _delete(condition, *_args, **_kwargs):
        module.settings.docStoreConn.deleted_inputs.append(condition)
        if not module.settings.docStoreConn.to_delete:
            return 0
        return module.settings.docStoreConn.to_delete.pop(0)

    module.settings.docStoreConn.to_delete = [0]
    monkeypatch.setattr(module.settings.docStoreConn, "delete", _delete)
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "chunk_ids": ["c1"]})
    res = _run(module.rm())
    assert res["message"] == "Index updating failure", res

    module.settings.docStoreConn.to_delete = [1, 2]
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "chunk_ids": ["c1", "c2", "c3"]})
    res = _run(module.rm())
    assert res["code"] == 0, res
    assert module.DocumentService.decrement_calls, "decrement_chunk_num should be called"
    assert len(module.settings.STORAGE_IMPL.rm_calls) >= 1

    module.settings.docStoreConn.to_delete = [1]
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "chunk_ids": "c1"})
    res = _run(module.rm())
    assert res["code"] == 0, res

    async def _raise_thread_pool(_func):
        raise RuntimeError("rm tp boom")

    monkeypatch.setattr(module, "thread_pool_exec", _raise_thread_pool)
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "chunk_ids": ["c1"]})
    res = _run(module.rm())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "rm tp boom" in res["message"], res