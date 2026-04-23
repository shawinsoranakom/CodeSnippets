def test_searchbots_related_questions_embedded_matrix_unit(monkeypatch):
    module = _load_session_module(monkeypatch)
    handler = inspect.unwrap(module.related_questions_embedded)

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer"}))
    res = _run(handler())
    assert res["message"] == "Authorization is not valid!"

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer bad"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [])
    res = _run(handler())
    assert "API key is invalid" in res["message"]

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer ok"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="")])
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"question": "q"}))
    res = _run(handler())
    assert res["message"] == "permission denined."

    captured = {}

    class _FakeChatBundle:
        async def async_chat(self, prompt, messages, options):
            captured["prompt"] = prompt
            captured["messages"] = messages
            captured["options"] = options
            return "1. Alpha\n2. Beta\nignored"

    def _fake_bundle(*args, **_kwargs):
        captured["bundle_args"] = args
        return _FakeChatBundle()

    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"question": "solar", "search_id": "search-1"}),
    )
    monkeypatch.setattr(
        module.SearchService,
        "get_detail",
        lambda _search_id: {"search_config": {"chat_id": "chat-x", "llm_setting": {"temperature": 0.2}}},
    )
    monkeypatch.setattr(module, "LLMBundle", _fake_bundle)
    res = _run(handler())
    assert res["code"] == 0
    assert res["data"] == ["Alpha", "Beta"]
    # LLMBundle is called with (tenant_id, model_config)
    # model_config is a dict with model_type, llm_name, etc.
    assert captured["bundle_args"][0] == "tenant-1"
    assert captured["bundle_args"][1].get("model_type") == module.LLMType.CHAT
    assert captured["bundle_args"][1].get("llm_name") == "chat-x"
    assert captured["options"] == {"temperature": 0.2}
    assert "Keywords: solar" in captured["messages"][0]["content"]