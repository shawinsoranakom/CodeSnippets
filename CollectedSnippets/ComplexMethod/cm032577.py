def test_run_branch_matrix_unit(self, document_app_module, monkeypatch):
        module = document_app_module
        calls = {"clear": [], "filter_delete": [], "docstore_delete": [], "cancel": [], "run": []}

        async def fake_thread_pool_exec(func, *args, **kwargs):
            return func(*args, **kwargs)

        monkeypatch.setattr(module, "thread_pool_exec", fake_thread_pool_exec)
        monkeypatch.setattr(module, "server_error_response", lambda e: {"code": 500, "message": str(e)})
        monkeypatch.setattr(module.search, "index_name", lambda tenant_id: f"idx_{tenant_id}")
        monkeypatch.setattr(module, "cancel_all_task_of", lambda doc_id: calls["cancel"].append(doc_id))

        class _DocStore:
            def index_exist(self, _index_name, _kb_id):
                return True

            def delete(self, where, _index_name, _kb_id):
                calls["docstore_delete"].append(where["doc_id"])

        monkeypatch.setattr(module.settings, "docStoreConn", _DocStore())

        async def set_request(payload):
            return payload

        def apply_request(payload):
            async def fake_request_json():
                return await set_request(payload)

            monkeypatch.setattr(module, "get_request_json", fake_request_json)

        apply_request({"doc_ids": ["doc1"], "run": module.TaskStatus.RUNNING.value})
        monkeypatch.setattr(module.DocumentService, "accessible", lambda *_args, **_kwargs: False)
        res = _run(module.run.__wrapped__())
        assert res["code"] == module.RetCode.AUTHENTICATION_ERROR

        monkeypatch.setattr(module.DocumentService, "accessible", lambda *_args, **_kwargs: True)
        monkeypatch.setattr(module.DocumentService, "get_tenant_id", lambda _doc_id: None)
        res = _run(module.run.__wrapped__())
        assert res["code"] == module.RetCode.DATA_ERROR
        assert "Tenant not found!" in res["message"]

        monkeypatch.setattr(module.DocumentService, "get_tenant_id", lambda _doc_id: "tenant1")
        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (False, None))
        res = _run(module.run.__wrapped__())
        assert res["code"] == module.RetCode.DATA_ERROR
        assert "Document not found!" in res["message"]

        apply_request({"doc_ids": ["doc1"], "run": module.TaskStatus.CANCEL.value})
        doc_cancel = SimpleNamespace(id="doc1", run=module.TaskStatus.DONE.value, kb_id="kb1", parser_config={}, to_dict=lambda: {"id": "doc1"})
        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (True, doc_cancel))
        monkeypatch.setattr(module.TaskService, "query", lambda **_kwargs: [SimpleNamespace(progress=1)])
        res = _run(module.run.__wrapped__())
        assert res["code"] == module.RetCode.DATA_ERROR
        assert "Cannot cancel a task that is not in RUNNING status" in res["message"]

        apply_request({"doc_ids": ["doc1"], "run": module.TaskStatus.RUNNING.value, "delete": True})
        doc_rerun = SimpleNamespace(id="doc1", run=module.TaskStatus.DONE.value, kb_id="kb1", parser_config={}, to_dict=lambda: {"id": "doc1"})
        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (True, doc_rerun))
        monkeypatch.setattr(module.DocumentService, "clear_chunk_num_when_rerun", lambda doc_id: calls["clear"].append(doc_id))
        monkeypatch.setattr(module.TaskService, "filter_delete", lambda _filters: calls["filter_delete"].append(True))
        monkeypatch.setattr(module.DocumentService, "update_by_id", lambda *_args, **_kwargs: True)
        monkeypatch.setattr(module.DocumentService, "run", lambda tenant_id, doc_dict, _kb_map: calls["run"].append((tenant_id, doc_dict)))
        res = _run(module.run.__wrapped__())
        assert res["code"] == 0
        assert calls["clear"] == ["doc1"]
        assert calls["filter_delete"] == [True]
        assert calls["docstore_delete"] == ["doc1"]
        assert calls["run"] == [("tenant1", {"id": "doc1"})]

        apply_request({"doc_ids": ["doc1"], "run": module.TaskStatus.RUNNING.value, "apply_kb": True})
        monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (False, None))
        res = _run(module.run.__wrapped__())
        assert res["code"] == 500
        assert "Can't find this dataset!" in res["message"]

        apply_request({"doc_ids": ["doc1"], "run": module.TaskStatus.RUNNING.value})

        def raise_run_error(*_args, **_kwargs):
            raise RuntimeError("run boom")

        monkeypatch.setattr(module.DocumentService, "run", raise_run_error)
        res = _run(module.run.__wrapped__())
        assert res["code"] == 500
        assert "run boom" in res["message"]