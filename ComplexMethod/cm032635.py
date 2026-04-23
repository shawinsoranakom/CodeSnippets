def test_list_app_grouping_availability_and_merge(monkeypatch):
    module = _load_llm_app(monkeypatch)

    ensure_calls = []
    monkeypatch.setattr(module.TenantLLMService, "ensure_mineru_from_env", lambda tenant_id: ensure_calls.append(tenant_id))

    tenant_rows = [
        _TenantLLMRow(id=1, llm_name="fast-emb", llm_factory="FastEmbed", model_type="embedding", api_key="k1", status="1"),
        _TenantLLMRow(id=2, llm_name="tenant-only", llm_factory="CustomFactory", model_type="chat", api_key="k2", status="1"),
    ]
    monkeypatch.setattr(module.TenantLLMService, "query", lambda **_kwargs: tenant_rows)

    all_llms = [
        _LLMRow(llm_name="tei-embed", fid="Builtin", model_type="embedding", status="1"),
        _LLMRow(llm_name="fast-emb", fid="FastEmbed", model_type="embedding", status="1"),
        _LLMRow(llm_name="not-in-status", fid="Other", model_type="chat", status="1"),
    ]
    monkeypatch.setattr(module.LLMService, "get_all", lambda: all_llms)

    monkeypatch.setattr(module, "request", SimpleNamespace(args={}))
    monkeypatch.setenv("COMPOSE_PROFILES", "tei-cpu")
    monkeypatch.setenv("TEI_MODEL", "tei-embed")

    res = _run(module.list_app())
    assert res["code"] == 0, res["message"]
    assert ensure_calls == ["tenant-1"]

    data = res["data"]
    assert {"Builtin", "FastEmbed", "CustomFactory"}.issubset(set(data.keys()))

    builtin = data["Builtin"][0]
    assert builtin["llm_name"] == "tei-embed"
    assert builtin["available"] is True

    fastembed = data["FastEmbed"][0]
    assert fastembed["llm_name"] == "fast-emb"
    assert fastembed["available"] is True

    tenant_only = data["CustomFactory"][0]
    assert tenant_only["llm_name"] == "tenant-only"
    assert tenant_only["available"] is True