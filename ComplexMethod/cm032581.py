def test_change_parser_guards_and_reset_update_failure_unit(self, document_app_module, monkeypatch):
        module = document_app_module

        monkeypatch.setattr(module, "server_error_response", lambda e: {"code": 500, "message": str(e)})

        async def req_auth_fail():
            return {"doc_id": "doc1", "parser_id": "naive", "pipeline_id": "pipe2"}

        monkeypatch.setattr(module, "get_request_json", req_auth_fail)
        monkeypatch.setattr(module.DocumentService, "accessible", lambda *_args, **_kwargs: False)
        res = _run(module.change_parser.__wrapped__())
        assert res["code"] == module.RetCode.AUTHENTICATION_ERROR

        monkeypatch.setattr(module.DocumentService, "accessible", lambda *_args, **_kwargs: True)
        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (False, None))
        res = _run(module.change_parser.__wrapped__())
        assert res["code"] == module.RetCode.DATA_ERROR
        assert "Document not found!" in res["message"]

        async def req_same_pipeline():
            return {"doc_id": "doc1", "parser_id": "naive", "pipeline_id": "pipe1"}

        doc_same = SimpleNamespace(
            id="doc1",
            pipeline_id="pipe1",
            parser_id="naive",
            parser_config={"k": "v"},
            token_num=0,
            chunk_num=0,
            process_duration=0,
            kb_id="kb1",
            type="doc",
            name="doc.txt",
        )
        monkeypatch.setattr(module, "get_request_json", req_same_pipeline)
        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (True, doc_same))
        res = _run(module.change_parser.__wrapped__())
        assert res["code"] == 0

        calls = []

        async def req_pipeline_change():
            return {"doc_id": "doc1", "parser_id": "naive", "pipeline_id": "pipe2"}

        doc = SimpleNamespace(
            id="doc1",
            pipeline_id="pipe1",
            parser_id="naive",
            parser_config={},
            token_num=0,
            chunk_num=0,
            process_duration=0,
            kb_id="kb1",
            type="doc",
            name="doc.txt",
        )

        def fake_update_by_id(doc_id, payload):
            calls.append((doc_id, payload))
            return True

        monkeypatch.setattr(module, "get_request_json", req_pipeline_change)
        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (True, doc))
        monkeypatch.setattr(module.DocumentService, "update_by_id", fake_update_by_id)
        res = _run(module.change_parser.__wrapped__())
        assert res["code"] == 0
        assert calls[0][1] == {"pipeline_id": "pipe2"}
        assert calls[1][1]["run"] == module.TaskStatus.UNSTART.value

        doc.token_num = 3
        doc.chunk_num = 2
        doc.process_duration = 9
        monkeypatch.setattr(module.DocumentService, "increment_chunk_num", lambda *_args, **_kwargs: False)
        res = _run(module.change_parser.__wrapped__())
        assert res["code"] == 0

        monkeypatch.setattr(module.DocumentService, "increment_chunk_num", lambda *_args, **_kwargs: True)
        monkeypatch.setattr(module.DocumentService, "get_tenant_id", lambda _doc_id: None)
        res = _run(module.change_parser.__wrapped__())
        assert res["code"] == 0

        side_effects = {"img": [], "delete": []}

        class _DocStore:
            def index_exist(self, _idx, _kb_id):
                return True

            def delete(self, where, _idx, kb_id):
                side_effects["delete"].append((where["doc_id"], kb_id))

        monkeypatch.setattr(module.DocumentService, "get_tenant_id", lambda _doc_id: "tenant1")
        monkeypatch.setattr(module.DocumentService, "delete_chunk_images", lambda _doc, _tenant: side_effects["img"].append((_doc.id, _tenant)))
        monkeypatch.setattr(module.search, "index_name", lambda tenant_id: f"idx_{tenant_id}")
        monkeypatch.setattr(module.settings, "docStoreConn", _DocStore())
        res = _run(module.change_parser.__wrapped__())
        assert res["code"] == 0
        assert ("doc1", "tenant1") in side_effects["img"]
        assert ("doc1", "kb1") in side_effects["delete"]

        async def req_same_parser_with_cfg():
            return {"doc_id": "doc1", "parser_id": "naive", "parser_config": {"a": 1}}

        doc_same_parser = SimpleNamespace(
            id="doc1",
            pipeline_id="pipe1",
            parser_id="naive",
            parser_config={"a": 1},
            token_num=0,
            chunk_num=0,
            process_duration=0,
            kb_id="kb1",
            type="doc",
            name="doc.txt",
        )
        monkeypatch.setattr(module, "get_request_json", req_same_parser_with_cfg)
        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (True, doc_same_parser))
        res = _run(module.change_parser.__wrapped__())
        assert res["code"] == 0

        async def req_same_parser_no_cfg():
            return {"doc_id": "doc1", "parser_id": "naive"}

        monkeypatch.setattr(module, "get_request_json", req_same_parser_no_cfg)
        res = _run(module.change_parser.__wrapped__())
        assert res["code"] == 0

        parser_cfg_updates = []

        async def req_parser_update():
            return {"doc_id": "doc1", "parser_id": "paper", "pipeline_id": "", "parser_config": {"beta": True}}

        doc_parser_update = SimpleNamespace(
            id="doc1",
            pipeline_id="pipe1",
            parser_id="naive",
            parser_config={"alpha": 1},
            token_num=0,
            chunk_num=0,
            process_duration=0,
            kb_id="kb1",
            type="doc",
            name="doc.txt",
        )
        monkeypatch.setattr(module, "get_request_json", req_parser_update)
        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (True, doc_parser_update))
        monkeypatch.setattr(module.DocumentService, "update_parser_config", lambda doc_id, cfg: parser_cfg_updates.append((doc_id, cfg)))
        monkeypatch.setattr(module.DocumentService, "update_by_id", lambda *_args, **_kwargs: True)
        res = _run(module.change_parser.__wrapped__())
        assert res["code"] == 0
        assert parser_cfg_updates == [("doc1", {"beta": True})]

        def raise_parser_config(*_args, **_kwargs):
            raise RuntimeError("parser boom")

        monkeypatch.setattr(module.DocumentService, "update_parser_config", raise_parser_config)
        res = _run(module.change_parser.__wrapped__())
        assert res["code"] == 500
        assert "parser boom" in res["message"]