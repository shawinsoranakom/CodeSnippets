def test_metadata_batch_update(self, monkeypatch):
        module = _load_doc_module(monkeypatch)
        monkeypatch.setattr(module, "convert_conditions", lambda cond: cond)
        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: False)
        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"selector": {}}))
        res = _run(module.metadata_batch_update.__wrapped__("ds-1", "tenant-1"))
        assert "don't own the dataset" in res["message"]

        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: True)
        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"selector": [1]}))
        res = _run(module.metadata_batch_update.__wrapped__("ds-1", "tenant-1"))
        assert res["message"] == "selector must be an object."

        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"selector": {}, "updates": {"k": "v"}, "deletes": []}))
        res = _run(module.metadata_batch_update.__wrapped__("ds-1", "tenant-1"))
        assert res["message"] == "updates and deletes must be lists."

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"selector": {"metadata_condition": [1]}, "updates": [], "deletes": []}),
        )
        res = _run(module.metadata_batch_update.__wrapped__("ds-1", "tenant-1"))
        assert res["message"] == "metadata_condition must be an object."

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"selector": {"document_ids": "doc-1"}, "updates": [], "deletes": []}),
        )
        res = _run(module.metadata_batch_update.__wrapped__("ds-1", "tenant-1"))
        assert res["message"] == "document_ids must be a list."

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"selector": {}, "updates": [{"key": ""}], "deletes": []}),
        )
        res = _run(module.metadata_batch_update.__wrapped__("ds-1", "tenant-1"))
        assert "Each update requires key and value." in res["message"]

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue({"selector": {}, "updates": [], "deletes": [{"x": "y"}]}),
        )
        res = _run(module.metadata_batch_update.__wrapped__("ds-1", "tenant-1"))
        assert "Each delete requires key." in res["message"]

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue(
                {
                    "selector": {"document_ids": ["bad"], "metadata_condition": {"conditions": []}},
                    "updates": [{"key": "k", "value": "v"}],
                    "deletes": [],
                }
            ),
        )
        monkeypatch.setattr(module.KnowledgebaseService, "list_documents_by_ids", lambda _ids: ["doc-1"])
        res = _run(module.metadata_batch_update.__wrapped__("ds-1", "tenant-1"))
        assert "do not belong to dataset" in res["message"]

        monkeypatch.setattr(
            module,
            "get_request_json",
            lambda: _AwaitableValue(
                {
                    "selector": {"document_ids": ["doc-1"], "metadata_condition": {"conditions": [{"f": "x"}]}},
                    "updates": [{"key": "k", "value": "v"}],
                    "deletes": [],
                }
            ),
        )
        monkeypatch.setattr(module, "meta_filter", lambda *_args, **_kwargs: [])
        monkeypatch.setattr(module.DocMetadataService, "get_flatted_meta_by_kbs", lambda _kbs: [])
        res = _run(module.metadata_batch_update.__wrapped__("ds-1", "tenant-1"))
        assert res["code"] == 0
        assert res["data"]["updated"] == 0
        assert res["data"]["matched_docs"] == 0

        monkeypatch.setattr(module, "meta_filter", lambda *_args, **_kwargs: ["doc-1"])
        monkeypatch.setattr(module.DocMetadataService, "batch_update_metadata", lambda *_args, **_kwargs: 1)
        res = _run(module.metadata_batch_update.__wrapped__("ds-1", "tenant-1"))
        assert res["code"] == 0
        assert res["data"]["updated"] == 1
        assert res["data"]["matched_docs"] == 1