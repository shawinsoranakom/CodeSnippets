def test_get_api_key_no_record_invalid_auth_api_error_generic_error_success(monkeypatch):
    module = _load_langfuse_app(monkeypatch)

    monkeypatch.setattr(module.TenantLangfuseService, "filter_by_tenant_with_info", lambda **_kwargs: None)
    res = module.get_api_key.__wrapped__()
    assert res["code"] == 0
    assert res["message"] == "Have not record any Langfuse keys."

    base_entry = {"secret_key": "sec", "public_key": "pub", "host": "http://host"}
    monkeypatch.setattr(module.TenantLangfuseService, "filter_by_tenant_with_info", lambda **_kwargs: dict(base_entry))
    monkeypatch.setattr(module, "Langfuse", lambda **_kwargs: _FakeLangfuseClient(auth_result=False))
    res = module.get_api_key.__wrapped__()
    assert res["code"] == 102
    assert res["message"] == "Invalid Langfuse keys loaded"

    monkeypatch.setattr(
        module,
        "Langfuse",
        lambda **_kwargs: _FakeLangfuseClient(auth_exc=_FakeApiError("api exploded")),
    )
    res = module.get_api_key.__wrapped__()
    assert res["code"] == 0
    assert "Error from Langfuse" in res["message"]

    monkeypatch.setattr(
        module,
        "Langfuse",
        lambda **_kwargs: _FakeLangfuseClient(auth_exc=RuntimeError("generic exploded")),
    )
    res = module.get_api_key.__wrapped__()
    assert res["code"] == 100
    assert "generic exploded" in res["message"]

    monkeypatch.setattr(module, "Langfuse", lambda **_kwargs: _FakeLangfuseClient(auth_result=True))
    res = module.get_api_key.__wrapped__()
    assert res["code"] == 0
    assert res["data"]["project_id"] == "project-id"
    assert res["data"]["project_name"] == "project-name"