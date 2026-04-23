def test_my_llms_include_details_and_exception_unit(monkeypatch):
    module = _load_llm_app(monkeypatch)
    monkeypatch.setattr(module, "request", SimpleNamespace(args={"include_details": "true"}))
    ensure_calls = []
    monkeypatch.setattr(module.TenantLLMService, "ensure_mineru_from_env", lambda tenant_id: ensure_calls.append(tenant_id))
    monkeypatch.setattr(
        module.TenantLLMService,
        "query",
        lambda **_kwargs: [
            _TenantLLMRow(
                id=1,
                llm_name="chat-model",
                llm_factory="FactoryX",
                model_type="chat",
                used_tokens=42,
                api_base="",
                max_tokens=4096,
                status="1",
            )
        ],
    )
    monkeypatch.setattr(module.LLMFactoriesService, "query", lambda **_kwargs: [SimpleNamespace(name="FactoryX", tags=["tag-a"])])
    res = module.my_llms()
    assert res["code"] == 0
    assert ensure_calls == ["tenant-1"]
    assert "FactoryX" in res["data"]
    assert res["data"]["FactoryX"]["tags"] == ["tag-a"]
    assert res["data"]["FactoryX"]["llm"][0]["used_token"] == 42
    assert res["data"]["FactoryX"]["llm"][0]["max_tokens"] == 4096

    monkeypatch.setattr(module.TenantLLMService, "ensure_mineru_from_env", lambda _tenant_id: (_ for _ in ()).throw(RuntimeError("my llms boom")))
    res = module.my_llms()
    assert res["code"] == 500
    assert "my llms boom" in res["message"]