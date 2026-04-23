def test_change_status_partial_failure_matrix_unit(self, document_app_module, monkeypatch):
        module = document_app_module
        calls = {"docstore_update": []}
        doc_ids = ["unauth", "missing_doc", "missing_kb", "update_fail", "docstore_3022", "docstore_generic", "outer_exc"]

        async def fake_request_json():
            return {"doc_ids": doc_ids, "status": "1"}

        def fake_accessible(doc_id, _uid):
            return doc_id != "unauth"

        def fake_get_by_id(doc_id):
            if doc_id == "missing_doc":
                return False, None
            if doc_id == "outer_exc":
                raise RuntimeError("explode")
            kb_id = "kb_missing" if doc_id == "missing_kb" else "kb1"
            chunk_num = 1 if doc_id in {"docstore_3022", "docstore_generic"} else 0
            doc = SimpleNamespace(id=doc_id, kb_id=kb_id, status="0", chunk_num=chunk_num)
            return True, doc

        def fake_get_kb(kb_id):
            if kb_id == "kb_missing":
                return False, None
            return True, SimpleNamespace(tenant_id="tenant1")

        def fake_update_by_id(doc_id, _payload):
            return doc_id != "update_fail"

        class _DocStore:
            def update(self, where, _payload, _index_name, _kb_id):
                calls["docstore_update"].append(where["doc_id"])
                if where["doc_id"] == "docstore_3022":
                    raise RuntimeError("3022 table missing")
                if where["doc_id"] == "docstore_generic":
                    raise RuntimeError("doc store down")
                return True

        monkeypatch.setattr(module, "get_request_json", fake_request_json)
        monkeypatch.setattr(module.DocumentService, "accessible", fake_accessible)
        monkeypatch.setattr(module.DocumentService, "get_by_id", fake_get_by_id)
        monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda kb_id: fake_get_kb(kb_id))
        monkeypatch.setattr(module.DocumentService, "update_by_id", fake_update_by_id)
        monkeypatch.setattr(module.settings, "docStoreConn", _DocStore())
        monkeypatch.setattr(module.search, "index_name", lambda tenant_id: f"idx_{tenant_id}")

        res = _run(module.change_status.__wrapped__())
        assert res["code"] == module.RetCode.SERVER_ERROR
        assert res["message"] == "Partial failure"
        assert res["data"]["unauth"]["error"] == "No authorization."
        assert res["data"]["missing_doc"]["error"] == "No authorization."
        assert res["data"]["missing_kb"]["error"] == "Can't find this dataset!"
        assert res["data"]["update_fail"]["error"] == "Database error (Document update)!"
        assert res["data"]["docstore_3022"]["error"] == "Document store table missing."
        assert "Document store update failed:" in res["data"]["docstore_generic"]["error"]
        assert "Internal server error: explode" == res["data"]["outer_exc"]["error"]
        assert calls["docstore_update"] == ["docstore_3022", "docstore_generic"]