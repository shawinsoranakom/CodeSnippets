def test_retrieval_validation_matrix(self, monkeypatch):
        module = _load_doc_module(monkeypatch)
        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"dataset_ids": "bad"}))
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert "`dataset_ids` should be a list" in res["message"]

        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"dataset_ids": ["ds-1"]}))
        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: False)
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert "don't own the dataset" in res["message"]

        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: True)
        monkeypatch.setattr(module.KnowledgebaseService, "get_by_ids", lambda _ids: [SimpleNamespace(embd_id="m1"), SimpleNamespace(embd_id="m2")])
        monkeypatch.setattr(module.TenantLLMService, "split_model_name_and_factory", lambda embd_id: (embd_id, "f"))
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert "different embedding models" in res["message"]

        monkeypatch.setattr(module.KnowledgebaseService, "get_by_ids", lambda _ids: [SimpleNamespace(embd_id="m1", tenant_id="tenant-1")])
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert "`question` is required." in res["message"]

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"dataset_ids": ["ds-1"], "question": "   "}),
        )
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert res["code"] == 0
        assert res["data"]["chunks"] == []

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"dataset_ids": ["ds-1"], "question": "q", "document_ids": "bad"}),
        )
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert "`documents` should be a list" in res["message"]

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"dataset_ids": ["ds-1"], "question": "q", "document_ids": ["not-owned"]}),
        )
        monkeypatch.setattr(module.KnowledgebaseService, "list_documents_by_ids", lambda _ids: ["doc-1"])
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert "don't own the document" in res["message"]

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"dataset_ids": ["ds-1"], "question": "q", "metadata_condition": {"logic": "and"}}),
        )
        monkeypatch.setattr(module.DocMetadataService, "get_flatted_meta_by_kbs", lambda _kbs: [])
        monkeypatch.setattr(module, "meta_filter", lambda *_args, **_kwargs: [])
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert "code" in res

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"dataset_ids": ["ds-1"], "question": "q", "highlight": "True"}),
        )
        monkeypatch.setattr(module.KnowledgebaseService, "get_by_ids", lambda _ids: [SimpleNamespace(embd_id="m1", tenant_id="tenant-1", tenant_embd_id=1)])
        monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _id: (True, SimpleNamespace(tenant_id="tenant-1", embd_id="m1", tenant_embd_id=1)))

        class _Retriever:
            async def retrieval(self, *_args, **_kwargs):
                return {"chunks": [], "total": 0}

            def retrieval_by_children(self, chunks, *_args, **_kwargs):
                return chunks

        monkeypatch.setattr(module, "LLMBundle", lambda *_args, **_kwargs: SimpleNamespace())
        monkeypatch.setattr(module, "label_question", lambda *_args, **_kwargs: {})
        monkeypatch.setattr(module.settings, "retriever", _Retriever())
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert res["code"] == 0, res["message"]
        assert res["data"]["chunks"] == []

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"dataset_ids": ["ds-1"], "question": "q", "highlight": True}),
        )
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert res["code"] == 0

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"dataset_ids": ["ds-1"], "question": "q", "highlight": "yes"}),
        )
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert "`highlight` should be a boolean" in res["message"]

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"dataset_ids": ["ds-1"], "question": "q", "highlight": 1}),
        )
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert "`highlight` should be a boolean" in res["message"]

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"dataset_ids": ["ds-1"], "question": "q"}),
        )
        monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _id: (False, None))
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert "Dataset not found!" in res["message"]

        feature_calls = {"cross": None, "keyword": None, "retrieval_question": None}

        async def _cross_languages(_tenant_id, _dialog, question, langs):
            feature_calls["cross"] = tuple(langs)
            return f"{question}-xl"

        async def _keyword_extraction(_chat_mdl, question):
            feature_calls["keyword"] = question
            return "-kw"

        class _FeatureRetriever:
            async def retrieval(self, question, *_args, **_kwargs):
                feature_calls["retrieval_question"] = question
                return {
                    "chunks": [
                        {
                            "chunk_id": "c1",
                            "content_with_weight": "content",
                            "doc_id": "doc-1",
                            "kb_id": "ds-1",
                            "vector": [1, 2],
                        }
                    ],
                    "total": 1,
                }

            async def retrieval_by_toc(self, question, chunks, tenant_ids, _chat_mdl, size):
                assert question == "q-xl-kw"
                assert chunks and tenant_ids
                assert size == 30
                return [
                    {
                        "chunk_id": "toc-1",
                        "content_with_weight": "toc content",
                        "doc_id": "doc-toc",
                        "kb_id": "ds-1",
                    }
                ]

            def retrieval_by_children(self, chunks, _tenant_ids):
                return chunks + [
                    {
                        "chunk_id": "child-1",
                        "content_with_weight": "child content",
                        "doc_id": "doc-child",
                        "kb_id": "ds-1",
                    }
                ]

        class _FeatureKgRetriever:
            async def retrieval(self, *_args, **_kwargs):
                return {
                    "chunk_id": "kg-1",
                    "content_with_weight": "kg content",
                    "doc_id": "doc-kg",
                    "kb_id": "ds-1",
                }

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue(
                {
                    "dataset_ids": ["ds-1"],
                    "question": "q",
                    "rerank_id": "rerank-1",
                    "cross_languages": ["fr"],
                    "keyword": True,
                    "toc_enhance": True,
                    "use_kg": True,
                }
            ),
        )
        monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _id: (True, SimpleNamespace(tenant_id="tenant-1", embd_id="m1", tenant_embd_id=1)))
        monkeypatch.setattr(module, "cross_languages", _cross_languages)
        monkeypatch.setattr(module, "keyword_extraction", _keyword_extraction)
        monkeypatch.setattr(module.settings, "retriever", _FeatureRetriever())
        monkeypatch.setattr(module.settings, "kg_retriever", _FeatureKgRetriever())
        monkeypatch.setattr(module, "label_question", lambda *_args, **_kwargs: {})
        monkeypatch.setattr(module, "LLMBundle", lambda *_args, **_kwargs: SimpleNamespace())
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert res["code"] == 0, res["message"]
        assert feature_calls["cross"] == ("fr",)
        assert feature_calls["keyword"] == "q-xl"
        assert feature_calls["retrieval_question"] == "q-xl-kw"
        assert res["data"]["chunks"][0]["id"] == "kg-1"
        assert res["data"]["chunks"][0]["content"] == "kg content"
        assert any(chunk["id"] == "toc-1" for chunk in res["data"]["chunks"])
        assert any(chunk["id"] == "child-1" for chunk in res["data"]["chunks"])

        class _NotFoundRetriever:
            async def retrieval(self, *_args, **_kwargs):
                raise Exception("boom not_found boom")

            def retrieval_by_children(self, chunks, *_args, **_kwargs):
                return chunks

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"dataset_ids": ["ds-1"], "question": "q"}),
        )
        monkeypatch.setattr(module.settings, "retriever", _NotFoundRetriever())
        res = _run(module.retrieval_test.__wrapped__("tenant-1"))
        assert res["code"] == module.RetCode.DATA_ERROR
        assert "No chunk found! Check the chunk status please!" in res["message"]