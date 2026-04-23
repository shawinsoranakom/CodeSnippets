def test_parse_branches(self, monkeypatch):
        module = _load_doc_module(monkeypatch)
        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: False)
        res = _run(module.parse.__wrapped__("tenant-1", "ds-1"))
        assert "don't own the dataset" in res["message"]

        monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: True)
        monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"document_ids": ["doc-1"]}))
        monkeypatch.setattr(module, "check_duplicate_ids", lambda ids, _kind: (ids, []))
        toggle_doc = _ToggleBoolDocList(_DummyDoc(progress=0))
        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: toggle_doc)
        res = _run(module.parse.__wrapped__("tenant-1", "ds-1"))
        assert "don't own the document" in res["message"]

        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [_DummyDoc(run=module.TaskStatus.RUNNING.value)])
        monkeypatch.setattr(
            module.DocumentService,
            "filter_update",
            lambda *_args, **_kwargs: 0,
        )
        res = _run(module.parse.__wrapped__("tenant-1", "ds-1"))
        assert "currently being processed" in res["message"]

        monkeypatch.setattr(module.DocumentService, "query", lambda **_kwargs: [_DummyDoc(progress=0)])
        monkeypatch.setattr(module.DocumentService, "filter_update", lambda *_args, **_kwargs: 1)
        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _id: (True, _DummyDoc()))
        monkeypatch.setattr(module.File2DocumentService, "get_storage_address", lambda **_kwargs: ("b", "n"))
        _patch_docstore(monkeypatch, module, delete=lambda *_args, **_kwargs: None)
        monkeypatch.setattr(module.TaskService, "filter_delete", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(module, "queue_tasks", lambda *_args, **_kwargs: None)
        monkeypatch.setattr(module, "check_duplicate_ids", lambda ids, _kind: (ids, ["Duplicate document ids: doc-1"]))
        res = _run(module.parse.__wrapped__("tenant-1", "ds-1"))
        assert res["code"] == 0
        assert res["data"]["success_count"] == 1
        assert "Duplicate document ids" in res["data"]["errors"][0]

        monkeypatch.setattr(module, "check_duplicate_ids", lambda _ids, _kind: ([], ["Duplicate document ids: doc-1"]))
        res = _run(module.parse.__wrapped__("tenant-1", "ds-1"))
        assert res["code"] == module.RetCode.DATA_ERROR
        assert "Duplicate document ids" in res["message"]