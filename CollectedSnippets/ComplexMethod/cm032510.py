def test_searchbots_retrieval_test_embedded_matrix_unit(monkeypatch):
    module = _load_session_module(monkeypatch)
    handler = inspect.unwrap(module.retrieval_test_embedded)

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer"}))
    res = _run(handler())
    assert res["message"] == "Authorization is not valid!"

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer invalid"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [])
    res = _run(handler())
    assert "API key is invalid" in res["message"]

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer ok"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"kb_id": [], "question": "q"}))
    res = _run(handler())
    assert res["message"] == "Please specify dataset firstly."

    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="")])
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"kb_id": "kb-1", "question": "q"}))
    res = _run(handler())
    assert res["message"] == "permission denined."

    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"kb_id": ["kb-no-access"], "question": "q"}))
    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-a")])
    monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: [])
    res = _run(handler())
    assert "Only owner of dataset authorized for this operation." in res["message"]

    llm_calls = []

    def _fake_llm_bundle(tenant_id, model_config, *args, **kwargs):
        # Extract llm_type from model_config for comparison
        llm_type = model_config.get("model_type") if isinstance(model_config, dict) else model_config
        llm_name = model_config.get("llm_name") if isinstance(model_config, dict) else None
        llm_calls.append((tenant_id, llm_type, llm_name, args, kwargs))
        return SimpleNamespace(tenant_id=tenant_id, llm_type=llm_type, llm_name=llm_name, args=args, kwargs=kwargs)

    monkeypatch.setattr(module, "LLMBundle", _fake_llm_bundle)
    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"kb_id": "kb-1", "question": "q", "meta_data_filter": {"method": "auto"}}),
    )
    monkeypatch.setattr(module.DocMetadataService, "get_flatted_meta_by_kbs", lambda _kb_ids: [{"id": "doc-1"}])

    async def _apply_filter(_meta_filter, _metas, _question, _chat_mdl, _local_doc_ids):
        return ["doc-filtered"]

    monkeypatch.setattr(module, "apply_meta_data_filter", _apply_filter)
    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-a")])
    monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: [SimpleNamespace(id="kb-1")])
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (False, None))
    res = _run(handler())
    assert res["message"] == "Knowledgebase not found!"
    assert any(call[1] == module.LLMType.CHAT for call in llm_calls)

    llm_calls.clear()
    retrieval_capture = {}

    async def _fake_retrieval(
        question,
        embd_mdl,
        tenant_ids,
        kb_ids,
        page,
        size,
        similarity_threshold,
        vector_similarity_weight,
        top,
        local_doc_ids,
        rerank_mdl=None,
        highlight=None,
        rank_feature=None,
    ):
        retrieval_capture.update(
            {
                "question": question,
                "embd_mdl": embd_mdl,
                "tenant_ids": tenant_ids,
                "kb_ids": kb_ids,
                "page": page,
                "size": size,
                "similarity_threshold": similarity_threshold,
                "vector_similarity_weight": vector_similarity_weight,
                "top": top,
                "local_doc_ids": local_doc_ids,
                "rerank_mdl": rerank_mdl,
                "highlight": highlight,
                "rank_feature": rank_feature,
            }
        )
        return {"chunks": [{"id": "chunk-1", "vector": [0.1]}]}

    async def _translate(_tenant_id, _chat_id, question, _langs):
        return question + "-translated"

    monkeypatch.setattr(module, "cross_languages", _translate)
    monkeypatch.setattr(module, "label_question", lambda _question, _kbs: ["label-1"])
    monkeypatch.setattr(module.settings, "retriever", SimpleNamespace(retrieval=_fake_retrieval))
    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue(
            {
                "kb_id": "kb-1",
                "question": "translated-q",
                "doc_ids": ["doc-seed"],
                "cross_languages": ["es"],
                "search_id": "search-1",
            }
        ),
    )
    monkeypatch.setattr(
        module.SearchService,
        "get_detail",
        lambda _search_id: {
            "search_config": {
                "meta_data_filter": {"method": "auto"},
                "chat_id": "chat-for-filter",
                "similarity_threshold": 0.42,
                "vector_similarity_weight": 0.8,
                "top_k": 7,
                "rerank_id": "reranker-model",
            }
        },
    )
    monkeypatch.setattr(module.DocMetadataService, "get_flatted_meta_by_kbs", lambda _kb_ids: [{"id": "doc-2"}])
    monkeypatch.setattr(module, "apply_meta_data_filter", _apply_filter)
    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-a")])
    monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: [SimpleNamespace(id="kb-1")])
    monkeypatch.setattr(
        module.KnowledgebaseService,
        "get_by_id",
        lambda _kb_id: (True, SimpleNamespace(tenant_id="tenant-kb", embd_id="embd-model", tenant_embd_id=None)),
    )
    res = _run(handler())
    assert res["code"] == 0
    assert res["data"]["labels"] == ["label-1"]
    assert "vector" not in res["data"]["chunks"][0]
    assert retrieval_capture["kb_ids"] == ["kb-1"]
    assert retrieval_capture["tenant_ids"] == ["tenant-a"]
    assert retrieval_capture["question"] == "translated-q-translated"
    assert retrieval_capture["similarity_threshold"] == 0.42
    assert retrieval_capture["vector_similarity_weight"] == 0.8
    assert retrieval_capture["top"] == 7
    assert retrieval_capture["local_doc_ids"] == ["doc-filtered"]
    assert retrieval_capture["rank_feature"] == ["label-1"]
    assert retrieval_capture["rerank_mdl"] is not None
    assert any(call[1] == module.LLMType.EMBEDDING.value and call[2] == "embd-model" for call in llm_calls)

    llm_calls.clear()

    async def _fake_keyword_extraction(_chat_mdl, question):
        return f"-{question}-keywords"

    async def _fake_kg_retrieval(question, tenant_ids, kb_ids, _embd_mdl, _chat_mdl):
        return {
            "id": "kg-chunk",
            "question": question,
            "tenant_ids": tenant_ids,
            "kb_ids": kb_ids,
            "content_with_weight": 1,
            "vector": [0.5],
        }

    monkeypatch.setattr(module, "keyword_extraction", _fake_keyword_extraction)
    monkeypatch.setattr(module.settings, "kg_retriever", SimpleNamespace(retrieval=_fake_kg_retrieval))
    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue(
            {
                "kb_id": "kb-1",
                "question": "keyword-q",
                "rerank_id": "manual-reranker",
                "keyword": True,
                "use_kg": True,
            }
        ),
    )
    monkeypatch.setattr(
        module.KnowledgebaseService,
        "get_by_id",
        lambda _kb_id: (True, SimpleNamespace(tenant_id="tenant-kb", embd_id="embd-model", tenant_embd_id=None)),
    )
    res = _run(handler())
    assert res["code"] == 0
    assert res["data"]["chunks"][0]["id"] == "kg-chunk"
    assert all("vector" not in chunk for chunk in res["data"]["chunks"])
    assert any(call[1] == module.LLMType.RERANK.value for call in llm_calls)

    async def _raise_not_found(*_args, **_kwargs):
        raise RuntimeError("x not_found y")

    monkeypatch.setattr(module.settings, "retriever", SimpleNamespace(retrieval=_raise_not_found))
    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"kb_id": "kb-1", "question": "q"}),
    )
    res = _run(handler())
    assert res["message"] == "No chunk found! Check the chunk status please!"