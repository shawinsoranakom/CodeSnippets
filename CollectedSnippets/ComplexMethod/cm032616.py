def test_create_chunk_guards_pagerank_and_success_unit(monkeypatch):
    module = _load_chunk_module(monkeypatch)
    module.request = SimpleNamespace(headers={"X-Request-ID": "req-1"}, args={})

    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "content_with_weight": "chunk", "important_kwd": "bad"})
    res = _run(module.create())
    assert res["message"] == "`important_kwd` is required to be a list", res

    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "content_with_weight": "chunk", "question_kwd": "bad"})
    res = _run(module.create())
    assert res["message"] == "`question_kwd` is required to be a list", res

    monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (False, None))
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "content_with_weight": "chunk"})
    res = _run(module.create())
    assert res["message"] == "Document not found!", res

    monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (True, _DummyDoc(doc_id="doc-1")))
    monkeypatch.setattr(module.DocumentService, "get_tenant_id", lambda _doc_id: "")
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "content_with_weight": "chunk"})
    res = _run(module.create())
    assert res["message"] == "Tenant not found!", res

    monkeypatch.setattr(module.DocumentService, "get_tenant_id", lambda _doc_id: "tenant-1")
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (False, None))
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "content_with_weight": "chunk"})
    res = _run(module.create())
    assert res["message"] == "Knowledgebase not found!", res

    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, SimpleNamespace(pagerank=0.8)))
    _set_request_json(
        monkeypatch,
        module,
        {"doc_id": "doc-1", "content_with_weight": "chunk", "tag_feas": [0.2]},
    )
    res = _run(module.create())
    assert "`tag_feas` must be an object mapping string tags to finite numeric scores" in res["message"], res

    _set_request_json(
        monkeypatch,
        module,
        {
            "doc_id": "doc-1",
            "content_with_weight": "chunk",
            "important_kwd": ["i1"],
            "question_kwd": ["q1"],
            "tag_feas": {"tag": 0.2},
        },
    )
    res = _run(module.create())
    assert res["code"] == 0, res
    assert res["data"]["chunk_id"], res
    assert module.settings.docStoreConn.inserted, "insert should be called"
    inserted = module.settings.docStoreConn.inserted[-1]
    assert "pagerank_flt" in inserted
    assert module.DocumentService.increment_calls, "increment_chunk_num should be called"

    async def _raise_thread_pool(_func):
        raise RuntimeError("create tp boom")

    monkeypatch.setattr(module, "thread_pool_exec", _raise_thread_pool)
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "content_with_weight": "chunk"})
    res = _run(module.create())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "create tp boom" in res["message"], res