def test_list_chunk_exception_branches_unit(monkeypatch):
    module = _load_chunk_module(monkeypatch)

    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "keywords": "chunk", "available_int": 0})
    res = _run(module.list_chunk())
    assert res["code"] == 0, res
    assert res["data"]["total"] == 1, res
    assert res["data"]["chunks"][0]["available_int"] == 1, res

    monkeypatch.setattr(module.DocumentService, "get_tenant_id", lambda _doc_id: "")
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1"})
    res = _run(module.list_chunk())
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert res["message"] == "Tenant not found!", res

    monkeypatch.setattr(module.DocumentService, "get_tenant_id", lambda _doc_id: "tenant-1")
    monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (False, None))
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1"})
    res = _run(module.list_chunk())
    assert res["message"] == "Document not found!", res

    async def _raise_not_found(*_args, **_kwargs):
        raise Exception("x not_found y")

    monkeypatch.setattr(module.settings.retriever, "search", _raise_not_found)
    monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (True, _DummyDoc()))
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1"})
    res = _run(module.list_chunk())
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert res["message"] == "No chunk found!", res

    async def _raise_generic(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(module.settings.retriever, "search", _raise_generic)
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1"})
    res = _run(module.list_chunk())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "boom" in res["message"], res