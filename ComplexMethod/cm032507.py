def test_chatbot_routes_auth_stream_nonstream_unit(monkeypatch):
    module = _load_session_module(monkeypatch)
    monkeypatch.setattr(module, "Response", _StubResponse)

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer"}))
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({}))
    res = _run(inspect.unwrap(module.chatbot_completions)("dialog-1"))
    assert res["message"] == "Authorization is not valid!"

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer bad"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [])
    res = _run(inspect.unwrap(module.chatbot_completions)("dialog-1"))
    assert "API key is invalid" in res["message"]

    stream_calls = []

    async def _iframe_stream(dialog_id, **req):
        stream_calls.append((dialog_id, dict(req)))
        yield "data:stream-chunk"

    monkeypatch.setattr(module, "iframe_completion", _iframe_stream)
    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer ok"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"stream": True}))
    resp = _run(inspect.unwrap(module.chatbot_completions)("dialog-1"))
    assert isinstance(resp, _StubResponse)
    assert resp.headers.get("Content-Type") == "text/event-stream; charset=utf-8"
    _run(_collect_stream(resp.body))
    assert stream_calls[-1][0] == "dialog-1"
    assert stream_calls[-1][1]["quote"] is False

    async def _iframe_nonstream(_dialog_id, **_req):
        yield {"answer": "non-stream"}

    monkeypatch.setattr(module, "iframe_completion", _iframe_nonstream)
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"stream": False, "quote": True}))
    res = _run(inspect.unwrap(module.chatbot_completions)("dialog-1"))
    assert res["data"]["answer"] == "non-stream"

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer"}))
    res = _run(inspect.unwrap(module.chatbots_inputs)("dialog-1"))
    assert res["message"] == "Authorization is not valid!"

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer invalid"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [])
    res = _run(inspect.unwrap(module.chatbots_inputs)("dialog-1"))
    assert "API key is invalid" in res["message"]

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer ok"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(module.DialogService, "get_by_id", lambda _dialog_id: (False, None))
    res = _run(inspect.unwrap(module.chatbots_inputs)("dialog-404"))
    assert res["message"] == "Can't find dialog by ID: dialog-404"