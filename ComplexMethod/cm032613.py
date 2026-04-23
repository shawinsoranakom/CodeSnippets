def test_get_chunk_sanitize_and_exception_matrix_unit(monkeypatch):
    module = _load_chunk_module(monkeypatch)
    module.request = SimpleNamespace(args={"chunk_id": "chunk-1"}, headers={})

    res = module.get()
    assert res["code"] == 0, res
    assert "q_2_vec" not in res["data"], res
    assert "content_tks" not in res["data"], res
    assert "content_ltks" not in res["data"], res
    assert "content_sm_ltks" not in res["data"], res

    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [])
    res = module.get()
    assert res["message"] == "Tenant not found!", res

    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [_DummyTenant("tenant-1")])
    module.settings.docStoreConn.chunk = None
    res = module.get()
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "Chunk not found" in res["message"], res

    def _raise_not_found(*_args, **_kwargs):
        raise Exception("NotFoundError: chunk-1")

    monkeypatch.setattr(module.settings.docStoreConn, "get", _raise_not_found)
    res = module.get()
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert res["message"] == "Chunk not found!", res

    def _raise_generic(*_args, **_kwargs):
        raise RuntimeError("get boom")

    monkeypatch.setattr(module.settings.docStoreConn, "get", _raise_generic)
    res = module.get()
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "get boom" in res["message"], res