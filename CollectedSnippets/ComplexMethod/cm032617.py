def test_retrieval_test_branch_matrix_unit(monkeypatch):
    module = _load_chunk_module(monkeypatch)
    module.request = SimpleNamespace(headers={"X-Request-ID": "req-r"}, args={})

    applied_filters = []
    llm_calls = []
    cross_calls = []
    keyword_calls = []

    async def _apply_filter(meta_data_filter, metas, question, chat_mdl, local_doc_ids):
        applied_filters.append(
            {
                "meta_data_filter": meta_data_filter,
                "metas": metas,
                "question": question,
                "chat_mdl": chat_mdl,
                "local_doc_ids": list(local_doc_ids),
            }
        )
        return ["doc-filtered"]

    async def _cross_languages(_tenant_id, _dialog, question, langs):
        cross_calls.append((question, tuple(langs)))
        return f"{question}-xl"

    async def _keyword_extraction(_chat_mdl, question):
        keyword_calls.append(question)
        return "-kw"

    class _Retriever:
        def __init__(self, mode="ok"):
            self.mode = mode
            self.retrieval_questions = []

        async def retrieval(self, question, *_args, **_kwargs):
            if self.mode == "not_found":
                raise Exception("boom not_found boom")
            if self.mode == "explode":
                raise RuntimeError("retrieval boom")
            self.retrieval_questions.append(question)
            return {"chunks": [{"id": "c1", "vector": [0.1], "content_with_weight": "chunk-content"}]}

        def retrieval_by_children(self, chunks, _tenant_ids):
            return list(chunks)

    class _KgRetriever:
        async def retrieval(self, *_args, **_kwargs):
            return {"id": "kg-1", "content_with_weight": "kg-content"}

    class _NoContentKgRetriever:
        async def retrieval(self, *_args, **_kwargs):
            return {"id": "kg-2", "content_with_weight": ""}

    monkeypatch.setattr(module, "LLMBundle", lambda *args, **kwargs: llm_calls.append((args, kwargs)) or SimpleNamespace())
    monkeypatch.setattr(module, "get_model_config_by_type_and_name", lambda *_args, **_kwargs: {"llm_name": "stub-model", "model_type": "chat"})
    monkeypatch.setattr(module, "get_tenant_default_model_by_type", lambda *_args, **_kwargs: {"llm_name": "stub-model", "model_type": "chat"})
    monkeypatch.setattr(module, "get_model_config_by_id", lambda *_args, **_kwargs: {"llm_name": "stub-model", "model_type": "embedding"})
    monkeypatch.setattr(module.DocMetadataService, "get_flatted_meta_by_kbs", lambda _kb_ids: [{"meta": "v"}], raising=False)
    monkeypatch.setattr(module, "apply_meta_data_filter", _apply_filter)
    monkeypatch.setattr(module.SearchService, "get_detail", lambda _sid: {"search_config": {"meta_data_filter": {"method": "auto"}, "chat_id": "chat-1"}}, raising=False)
    monkeypatch.setattr(module, "cross_languages", _cross_languages)
    monkeypatch.setattr(module, "keyword_extraction", _keyword_extraction)
    monkeypatch.setattr(module, "label_question", lambda *_args, **_kwargs: ["lbl"])
    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [_DummyTenant("tenant-1")])

    monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: False, raising=False)
    _set_request_json(monkeypatch, module, {"kb_id": "kb-1", "question": "q", "search_id": "search-1"})
    res = _run(module.retrieval_test())
    assert res["code"] == module.RetCode.OPERATING_ERROR, res
    assert "Only owner of dataset authorized for this operation." in res["message"], res
    assert applied_filters and applied_filters[-1]["meta_data_filter"]["method"] == "auto"
    assert llm_calls, "search_id metadata auto branch should instantiate chat model"

    _set_request_json(monkeypatch, module, {"kb_id": [], "question": "q"})
    res = _run(module.retrieval_test())
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "Please specify dataset firstly." in res["message"], res

    monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: True, raising=False)
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (False, None), raising=False)
    _set_request_json(
        monkeypatch,
        module,
        {"kb_id": ["kb-1"], "question": "q", "meta_data_filter": {"method": "semi_auto"}},
    )
    res = _run(module.retrieval_test())
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "Knowledgebase not found!" in res["message"], res

    retriever = _Retriever(mode="ok")
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, SimpleNamespace(tenant_id="tenant-kb", embd_id="embd-1", tenant_embd_id=2)), raising=False)
    monkeypatch.setattr(module.settings, "retriever", retriever)
    monkeypatch.setattr(module.settings, "kg_retriever", _KgRetriever(), raising=False)
    _set_request_json(
        monkeypatch,
        module,
        {
            "kb_id": ["kb-1"],
            "question": "q",
            "cross_languages": ["fr"],
            "rerank_id": "rerank-1",
            "keyword": True,
            "use_kg": True,
        },
    )
    res = _run(module.retrieval_test())
    assert res["code"] == 0, res
    assert cross_calls[-1] == ("q", ("fr",))
    assert keyword_calls[-1] == "q-xl"
    assert retriever.retrieval_questions[-1] == "q-xl-kw"
    assert res["data"]["chunks"][0]["id"] == "kg-1", res
    assert all("vector" not in chunk for chunk in res["data"]["chunks"])

    monkeypatch.setattr(module.settings, "kg_retriever", _NoContentKgRetriever(), raising=False)
    _set_request_json(monkeypatch, module, {"kb_id": ["kb-1"], "question": "q", "use_kg": True})
    res = _run(module.retrieval_test())
    assert res["code"] == 0, res
    assert res["data"]["chunks"][0]["id"] == "c1", res

    monkeypatch.setattr(module.settings, "retriever", _Retriever(mode="not_found"))
    _set_request_json(monkeypatch, module, {"kb_id": ["kb-1"], "question": "q"})
    res = _run(module.retrieval_test())
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "No chunk found! Check the chunk status please!" in res["message"], res

    monkeypatch.setattr(module.settings, "retriever", _Retriever(mode="explode"))
    _set_request_json(monkeypatch, module, {"kb_id": ["kb-1"], "question": "q"})
    res = _run(module.retrieval_test())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "retrieval boom" in res["message"], res