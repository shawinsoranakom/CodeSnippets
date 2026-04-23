def test_update_chunk_branches(self, monkeypatch):
        module = _load_doc_module(monkeypatch)
        _patch_docstore(monkeypatch, module, get=lambda *_args, **_kwargs: None)
        res = _run(module.update_chunk.__wrapped__("tenant-1", "ds-1", "doc-1", "chunk-1"))
        assert "Can't find this chunk" in res["message"]

        _patch_docstore(monkeypatch, module, get=lambda *_args, **_kwargs: {"content_with_weight": "q\na"})
        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: False)
        res = _run(module.update_chunk.__wrapped__("tenant-1", "ds-1", "doc-1", "chunk-1"))
        assert "don't own the dataset" in res["message"]

        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: True)
        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [])
        res = _run(module.update_chunk.__wrapped__("tenant-1", "ds-1", "doc-1", "chunk-1"))
        assert "don't own the document" in res["message"]

        doc = _DummyDoc(parser_id="naive")
        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [doc])
        monkeypatch.setattr(module.rag_tokenizer, "tokenize", lambda text: text or "")
        monkeypatch.setattr(module.rag_tokenizer, "fine_grained_tokenize", lambda text: text or "")
        monkeypatch.setattr(module.rag_tokenizer, "is_chinese", lambda _text: False)
        monkeypatch.setattr(module.DocumentService, "get_embd_id", lambda _doc_id: "embd")
        monkeypatch.setattr(module.DocumentService, "get_tenant_embd_id", lambda _doc_id: 1)

        class _EmbedModel:
            def encode(self, _texts):
                return [np.array([0.2, 0.8]), np.array([0.3, 0.7])], 1

        monkeypatch.setattr(module.TenantLLMService, "model_instance", lambda *_args, **_kwargs: _EmbedModel())
        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"positions": "bad"}))
        res = _run(module.update_chunk.__wrapped__("tenant-1", "ds-1", "doc-1", "chunk-1"))
        assert "`positions` should be a list" in res["message"]

        _patch_docstore(monkeypatch, module, get=lambda *_args, **_kwargs: {"content_with_weight": "x"}, update=lambda *_args, **_kwargs: None)
        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"positions": [[1, 2, 3, 4, 5]]}))
        res = _run(module.update_chunk.__wrapped__("tenant-1", "ds-1", "doc-1", "chunk-1"))
        assert res["code"] == 0

        qa_doc = _DummyDoc(parser_id=module.ParserType.QA)
        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [qa_doc])
        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"content": "no-separator"}))
        res = _run(module.update_chunk.__wrapped__("tenant-1", "ds-1", "doc-1", "chunk-1"))
        assert "Q&A must be separated" in res["message"]

        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"content": "Q?\nA!"}))
        _patch_docstore(monkeypatch, module, get=lambda *_args, **_kwargs: {"content_with_weight": "Q?\nA!"}, update=lambda *_args, **_kwargs: None)
        monkeypatch.setattr(module, "beAdoc", lambda d, *_args, **_kwargs: d)
        res = _run(module.update_chunk.__wrapped__("tenant-1", "ds-1", "doc-1", "chunk-1"))
        assert res["code"] == 0