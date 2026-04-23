def test_llm_mutation_routes_unit(monkeypatch):
    module = _load_llm_app(monkeypatch)
    calls = {"delete": [], "update": []}
    monkeypatch.setattr(module.TenantLLMService, "filter_delete", lambda filters: calls["delete"].append(filters) or True)
    monkeypatch.setattr(module.TenantLLMService, "filter_update", lambda filters, payload: calls["update"].append((filters, payload)) or True)

    _set_request_json(monkeypatch, module, {"llm_factory": "OpenAI", "llm_name": "gpt"})
    res = _run(module.delete_llm())
    assert res["code"] == 0
    assert res["data"] is True

    _set_request_json(monkeypatch, module, {"llm_factory": "OpenAI", "llm_name": "gpt", "status": 0})
    res = _run(module.enable_llm())
    assert res["code"] == 0
    assert res["data"] is True
    assert calls["update"][0][1]["status"] == "0"

    _set_request_json(monkeypatch, module, {"llm_factory": "OpenAI"})
    res = _run(module.delete_factory())
    assert res["code"] == 0
    assert res["data"] is True
    assert len(calls["delete"]) == 2