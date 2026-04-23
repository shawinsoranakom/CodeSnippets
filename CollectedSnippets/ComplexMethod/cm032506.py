def test_sessions_related_questions_prompt_build_unit(monkeypatch):
    module = _load_session_module(monkeypatch)

    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({}))
    res = _run(inspect.unwrap(module.related_questions)("tenant-1"))
    assert res["message"] == "`question` is required."

    captured = {}

    class _FakeLLMBundle:
        def __init__(self, *args, **kwargs):
            captured["bundle_args"] = args
            captured["bundle_kwargs"] = kwargs

        async def async_chat(self, prompt, messages, options):
            captured["prompt"] = prompt
            captured["messages"] = messages
            captured["options"] = options
            return "1. First related\n2. Second related\nplain text"

    monkeypatch.setattr(module, "LLMBundle", _FakeLLMBundle)
    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"question": "solar energy", "industry": "renewables"}),
    )
    res = _run(inspect.unwrap(module.related_questions)("tenant-1"))
    assert res["data"] == ["First related", "Second related"]
    assert "Keep the term length between 2-4 words" in captured["prompt"]
    assert "related terms can also help search engines" in captured["prompt"]
    assert "Ensure all search terms are relevant to the industry: renewables." in captured["prompt"]
    assert "Keywords: solar energy" in captured["messages"][0]["content"]
    assert captured["options"] == {"temperature": 0.9}