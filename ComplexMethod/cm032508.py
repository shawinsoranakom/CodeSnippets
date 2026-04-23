def test_agentbot_routes_auth_stream_nonstream_unit(monkeypatch):
    module = _load_session_module(monkeypatch)
    monkeypatch.setattr(module, "Response", _StubResponse)

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer"}))
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({}))
    res = _run(inspect.unwrap(module.agent_bot_completions)("agent-1"))
    assert res["message"] == "Authorization is not valid!"

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer bad"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [])
    res = _run(inspect.unwrap(module.agent_bot_completions)("agent-1"))
    assert "API key is invalid" in res["message"]

    async def _agent_stream(*_args, **_kwargs):
        yield "data:agent-stream"

    monkeypatch.setattr(module, "agent_completion", _agent_stream)
    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer ok"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"stream": True}))
    resp = _run(inspect.unwrap(module.agent_bot_completions)("agent-1"))
    assert isinstance(resp, _StubResponse)
    assert resp.headers.get("Content-Type") == "text/event-stream; charset=utf-8"
    _run(_collect_stream(resp.body))

    async def _agent_nonstream(*_args, **_kwargs):
        yield {"answer": "agent-non-stream"}

    monkeypatch.setattr(module, "agent_completion", _agent_nonstream)
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"stream": False}))
    res = _run(inspect.unwrap(module.agent_bot_completions)("agent-1"))
    assert res["data"]["answer"] == "agent-non-stream"

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer"}))
    res = _run(inspect.unwrap(module.begin_inputs)("agent-1"))
    assert res["message"] == "Authorization is not valid!"

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer bad"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [])
    res = _run(inspect.unwrap(module.begin_inputs)("agent-1"))
    assert "API key is invalid" in res["message"]

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer ok"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _agent_id: (False, None))
    res = _run(inspect.unwrap(module.begin_inputs)("agent-404"))
    assert res["message"] == "Can't find agent by ID: agent-404"