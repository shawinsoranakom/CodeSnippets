def test_agents_openai_compatibility_unit(monkeypatch):
    module = _load_session_module(monkeypatch)

    monkeypatch.setattr(module, "Response", _StubResponse)
    monkeypatch.setattr(module, "jsonify", lambda payload: payload)
    monkeypatch.setattr(module, "num_tokens_from_string", lambda text: len(text or ""))

    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"model": "model", "messages": []}))
    res = _run(inspect.unwrap(module.agents_completion_openai_compatibility)("tenant-1", "agent-1"))
    assert "at least one message" in res["message"]

    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"model": "model", "messages": [{"role": "user", "content": "hello"}]}),
    )
    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [])
    res = _run(inspect.unwrap(module.agents_completion_openai_compatibility)("tenant-1", "agent-1"))
    assert "don't own the agent" in res["message"]

    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [SimpleNamespace(id="agent-1")])
    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"model": "model", "messages": [{"role": "system", "content": "system only"}]}),
    )
    res = _run(inspect.unwrap(module.agents_completion_openai_compatibility)("tenant-1", "agent-1"))
    assert "No valid messages found" in json.dumps(res)

    captured_calls = []

    async def _completion_openai_stream(*args, **kwargs):
        captured_calls.append((args, kwargs))
        yield "data:stream"

    monkeypatch.setattr(module, "completion_openai", _completion_openai_stream)
    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue(
            {
                "model": "model",
                "messages": [
                    {"role": "assistant", "content": "preface"},
                    {"role": "user", "content": "latest question"},
                ],
                "stream": True,
                "metadata": {"id": "meta-session"},
            }
        ),
    )
    resp = _run(inspect.unwrap(module.agents_completion_openai_compatibility)("tenant-1", "agent-1"))
    assert isinstance(resp, _StubResponse)
    assert resp.headers.get("Content-Type") == "text/event-stream; charset=utf-8"
    _run(_collect_stream(resp.body))
    assert captured_calls[-1][0][2] == "latest question"

    async def _completion_openai_nonstream(*args, **kwargs):
        captured_calls.append((args, kwargs))
        yield {"id": "non-stream"}

    monkeypatch.setattr(module, "completion_openai", _completion_openai_nonstream)
    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue(
            {
                "model": "model",
                "messages": [
                    {"role": "user", "content": "first"},
                    {"role": "assistant", "content": "middle"},
                    {"role": "user", "content": "final user"},
                ],
                "stream": False,
                "session_id": "session-1",
                "temperature": 0.5,
            }
        ),
    )
    res = _run(inspect.unwrap(module.agents_completion_openai_compatibility)("tenant-1", "agent-1"))
    assert res["id"] == "non-stream"
    assert captured_calls[-1][0][2] == "final user"
    assert captured_calls[-1][1]["stream"] is False
    assert captured_calls[-1][1]["session_id"] == "session-1"