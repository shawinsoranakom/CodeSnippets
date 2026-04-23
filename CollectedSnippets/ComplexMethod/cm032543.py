def test_download_and_download_doc_errors(self, monkeypatch):
        module = _load_doc_module(monkeypatch)
        _patch_send_file(monkeypatch, module)
        _patch_storage(monkeypatch, module, file_stream=b"")
        res = _run(module.download.__wrapped__("tenant-1", "ds-1", ""))
        assert res["message"] == "Specify document_id please."
        monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: [])
        res = _run(module.download.__wrapped__("tenant-1", "ds-1", "doc-1"))
        assert "do not own the dataset" in res["message"]

        monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: [1])
        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [])
        res = _run(module.download.__wrapped__("tenant-1", "ds-1", "doc-1"))
        assert "not own the document" in res["message"]

        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [_DummyDoc()])
        monkeypatch.setattr(module.File2DocumentService, "get_storage_address", lambda **_kwargs: ("b", "n"))
        res = _run(module.download.__wrapped__("tenant-1", "ds-1", "doc-1"))
        assert res["message"] == "This file is empty."

        monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer"}))
        res = _run(module.download_doc("doc-1"))
        assert "Authorization is not valid" in res["message"]

        monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer token"}))
        monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [])
        res = _run(module.download_doc("doc-1"))
        assert "API key is invalid" in res["message"]

        monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace()])
        res = _run(module.download_doc(""))
        assert res["message"] == "Specify document_id please."

        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [])
        res = _run(module.download_doc("doc-1"))
        assert "not own the document" in res["message"]

        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [_DummyDoc()])
        monkeypatch.setattr(module.File2DocumentService, "get_storage_address", lambda **_kwargs: ("b", "n"))
        _patch_storage(monkeypatch, module, file_stream=b"")
        res = _run(module.download_doc("doc-1"))
        assert res["message"] == "This file is empty."

        _patch_storage(monkeypatch, module, file_stream=b"abc")
        res = _run(module.download_doc("doc-1"))
        assert res["filename"] == "doc.txt"