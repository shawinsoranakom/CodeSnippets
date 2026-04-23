def test_thumbnails_missing_ids_rewrite_and_exception_unit(self, document_app_module, monkeypatch):
        module = document_app_module
        monkeypatch.setattr(module, "request", _DummyRequest(args={}))
        res = module.thumbnails()
        assert res["code"] == module.RetCode.ARGUMENT_ERROR
        assert 'Lack of "Document ID"' in res["message"]

        monkeypatch.setattr(module, "request", _DummyRequest(args={"doc_ids": ["doc1", "doc2"]}))
        monkeypatch.setattr(
            module.DocumentService,
            "get_thumbnails",
            lambda _doc_ids: [
                {"id": "doc1", "kb_id": "kb1", "thumbnail": "thumb.jpg"},
                {"id": "doc2", "kb_id": "kb1", "thumbnail": f"{module.IMG_BASE64_PREFIX}blob"},
            ],
        )
        res = module.thumbnails()
        assert res["code"] == 0
        assert res["data"]["doc1"] == "/v1/document/image/kb1-thumb.jpg"
        assert res["data"]["doc2"] == f"{module.IMG_BASE64_PREFIX}blob"

        def raise_error(*_args, **_kwargs):
            raise RuntimeError("thumb boom")

        monkeypatch.setattr(module.DocumentService, "get_thumbnails", raise_error)
        monkeypatch.setattr(module, "server_error_response", lambda e: {"code": 500, "message": str(e)})
        res = module.thumbnails()
        assert res["code"] == 500
        assert "thumb boom" in res["message"]