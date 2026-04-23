def test_stop_parsing_branches(self, monkeypatch):
        module = _load_doc_module(monkeypatch)
        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: False)
        res = _run(module.stop_parsing.__wrapped__("tenant-1", "ds-1"))
        assert "don't own the dataset" in res["message"]

        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: True)
        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({}))
        res = _run(module.stop_parsing.__wrapped__("tenant-1", "ds-1"))
        assert "`document_ids` is required" in res["message"]

        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"document_ids": ["doc-1"]}))
        monkeypatch.setattr(module, "check_duplicate_ids", lambda ids, _kind: (ids, []))
        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [])
        res = _run(module.stop_parsing.__wrapped__("tenant-1", "ds-1"))
        assert "don't own the document" in res["message"]

        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [_DummyDoc(run=module.TaskStatus.DONE.value)])
        monkeypatch.setattr(
            module,
            "cancel_all_task_of",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("cancel_all_task_of must not be called for non-running docs")),
        )
        monkeypatch.setattr(
            module.DocumentService,
            "update_by_id",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("update_by_id must not be called for non-running docs")),
        )
        res = _run(module.stop_parsing.__wrapped__("tenant-1", "ds-1"))
        assert res["code"] == module.RetCode.DATA_ERROR
        assert res["data"]["error_code"] == module.DOC_STOP_PARSING_INVALID_STATE_ERROR_CODE
        assert res["message"] == module.DOC_STOP_PARSING_INVALID_STATE_MESSAGE

        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [_DummyDoc(run=module.TaskStatus.RUNNING.value)])
        monkeypatch.setattr(module, "cancel_all_task_of", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(module.DocumentService, "update_by_id", lambda *_args, **_kwargs: True)
        _patch_docstore(monkeypatch, module, delete=lambda *_args, **_kwargs: None)
        monkeypatch.setattr(module, "check_duplicate_ids", lambda ids, _kind: (ids, ["Duplicate document ids: doc-1"]))
        res = _run(module.stop_parsing.__wrapped__("tenant-1", "ds-1"))
        assert res["code"] == 0
        assert res["data"]["success_count"] == 1
        assert "Duplicate document ids" in res["data"]["errors"][0]

        monkeypatch.setattr(module, "check_duplicate_ids", lambda _ids, _kind: ([], ["Duplicate document ids: doc-1"]))
        res = _run(module.stop_parsing.__wrapped__("tenant-1", "ds-1"))
        assert res["code"] == module.RetCode.DATA_ERROR
        assert "Duplicate document ids" in res["message"]

        monkeypatch.setattr(module, "check_duplicate_ids", lambda ids, _kind: (ids, []))
        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [_DummyDoc(run=module.TaskStatus.RUNNING.value)])
        res = _run(module.stop_parsing.__wrapped__("tenant-1", "ds-1"))
        assert res["code"] == 0