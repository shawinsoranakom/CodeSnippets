def test_set_chunk_bytes_qa_image_and_guard_matrix_unit(monkeypatch):
    module = _load_chunk_module(monkeypatch)

    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "chunk_id": "chunk-1", "content_with_weight": 1})
    with pytest.raises(TypeError, match="expected string or bytes-like object"):
        _run(module.set())

    _set_request_json(
        monkeypatch,
        module,
        {"doc_id": "doc-1", "chunk_id": "chunk-1", "content_with_weight": "abc", "important_kwd": "bad"},
    )
    res = _run(module.set())
    assert res["message"] == "`important_kwd` should be a list", res

    _set_request_json(
        monkeypatch,
        module,
        {"doc_id": "doc-1", "chunk_id": "chunk-1", "content_with_weight": "abc", "question_kwd": "bad"},
    )
    res = _run(module.set())
    assert res["message"] == "`question_kwd` should be a list", res

    monkeypatch.setattr(module.DocumentService, "get_tenant_id", lambda _doc_id: "")
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "chunk_id": "chunk-1", "content_with_weight": "abc"})
    res = _run(module.set())
    assert res["message"] == "Tenant not found!", res

    monkeypatch.setattr(module.DocumentService, "get_tenant_id", lambda _doc_id: "tenant-1")
    monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (False, None))
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "chunk_id": "chunk-1", "content_with_weight": "abc"})
    res = _run(module.set())
    assert res["message"] == "Document not found!", res

    monkeypatch.setattr(
        module.DocumentService,
        "get_by_id",
        lambda _doc_id: (True, _DummyDoc(doc_id="doc-1", parser_id=module.ParserType.NAIVE)),
    )
    _set_request_json(
        monkeypatch,
        module,
        {"doc_id": "doc-1", "chunk_id": "chunk-1", "content_with_weight": "abc", "tag_feas": [0.1]},
    )
    res = _run(module.set())
    assert "`tag_feas` must be an object mapping string tags to finite numeric scores" in res["message"], res

    _set_request_json(
        monkeypatch,
        module,
        {
            "doc_id": "doc-1",
            "chunk_id": "chunk-1",
            "content_with_weight": b"bytes-content",
            "important_kwd": ["important"],
            "question_kwd": ["question"],
            "tag_kwd": ["tag"],
            "tag_feas": {"tag": 0.1},
            "available_int": 0,
        },
    )
    res = _run(module.set())
    assert res["code"] == 0, res
    assert module.settings.docStoreConn.updated[-1][1]["content_with_weight"] == "bytes-content"

    monkeypatch.setattr(
        module.DocumentService,
        "get_by_id",
        lambda _doc_id: (True, _DummyDoc(doc_id="doc-1", parser_id=module.ParserType.QA)),
    )
    _set_request_json(
        monkeypatch,
        module,
        {
            "doc_id": "doc-1",
            "chunk_id": "chunk-2",
            "content_with_weight": "Q:Question\nA:Answer",
            "image_base64": base64.b64encode(b"image").decode("utf-8"),
            "img_id": "bucket-name",
        },
    )
    res = _run(module.set())
    assert res["code"] == 0, res
    assert module.settings.STORAGE_IMPL.put_calls, "image storage branch should be called"

    async def _raise_thread_pool(_func):
        raise RuntimeError("set tp boom")

    monkeypatch.setattr(module, "thread_pool_exec", _raise_thread_pool)
    _set_request_json(monkeypatch, module, {"doc_id": "doc-1", "chunk_id": "chunk-1", "content_with_weight": "abc"})
    res = _run(module.set())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "set tp boom" in res["message"], res