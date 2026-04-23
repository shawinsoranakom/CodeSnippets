def test_list_chunks_branches(self, monkeypatch):
        module = _load_doc_module(monkeypatch)
        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: False)
        res = _run(module.list_chunks.__wrapped__("tenant-1", "ds-1", "doc-1"))
        assert "don't own the dataset" in res["message"]

        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: True)
        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [])
        res = _run(module.list_chunks.__wrapped__("tenant-1", "ds-1", "doc-1"))
        assert "don't own the document" in res["message"]

        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [_DummyDoc()])
        monkeypatch.setattr(module, "request", SimpleNamespace(args=_DummyArgs({"id": "chunk-1"})))
        _patch_docstore(monkeypatch, module, get=lambda *_args, **_kwargs: None)
        res = _run(module.list_chunks.__wrapped__("tenant-1", "ds-1", "doc-1"))
        assert "Chunk not found" in res["message"]

        _patch_docstore(monkeypatch, module, get=lambda *_args, **_kwargs: {"id_vec": [1], "content_with_weight_vec": [2]})
        res = _run(module.list_chunks.__wrapped__("tenant-1", "ds-1", "doc-1"))
        assert "Chunk `chunk-1` not found." in res["message"]

        _patch_docstore(
            monkeypatch,
            module,
            get=lambda *_args, **_kwargs: {
                "chunk_id": "chunk-1",
                "content_with_weight": "x",
                "doc_id": "doc-1",
                "docnm_kwd": "doc",
                "position_int": [[1, 2, 3, 4, 5]],
            },
        )
        res = _run(module.list_chunks.__wrapped__("tenant-1", "ds-1", "doc-1"))
        assert res["code"] == 0
        assert res["data"]["total"] == 1
        assert res["data"]["chunks"][0]["id"] == "chunk-1"