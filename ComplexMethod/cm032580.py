def test_get_route_not_found_success_and_exception_unit(self, document_app_module, monkeypatch):
        module = document_app_module
        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (False, None))
        res = _run(module.get("doc1"))
        assert res["code"] == module.RetCode.DATA_ERROR
        assert "Document not found!" in res["message"]

        async def fake_thread_pool_exec(*_args, **_kwargs):
            return b"blob-data"

        async def fake_make_response(data):
            return _DummyResponse(data)

        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (True, SimpleNamespace(name="image.abc", type=module.FileType.VISUAL.value)))
        monkeypatch.setattr(module.File2DocumentService, "get_storage_address", lambda **_kwargs: ("bucket", "name"))
        monkeypatch.setattr(module.settings, "STORAGE_IMPL", SimpleNamespace(get=lambda *_args, **_kwargs: b"blob-data"))
        monkeypatch.setattr(module, "thread_pool_exec", fake_thread_pool_exec)
        monkeypatch.setattr(module, "make_response", fake_make_response)
        monkeypatch.setattr(
            module,
            "apply_safe_file_response_headers",
            lambda response, content_type, extension: response.headers.update({"content_type": content_type, "extension": extension}),
        )
        res = _run(module.get("doc1"))
        assert isinstance(res, _DummyResponse)
        assert res.data == b"blob-data"
        assert res.headers["content_type"] == "image/abc"
        assert res.headers["extension"] == "abc"

        monkeypatch.setattr(module.DocumentService, "get_by_id", lambda _doc_id: (_ for _ in ()).throw(RuntimeError("get boom")))
        monkeypatch.setattr(module, "server_error_response", lambda e: {"code": 500, "message": str(e)})
        res = _run(module.get("doc1"))
        assert res["code"] == 500
        assert "get boom" in res["message"]