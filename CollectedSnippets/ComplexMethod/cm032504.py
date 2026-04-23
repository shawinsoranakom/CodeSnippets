def test_agent_completions_stream_and_nonstream_unit(monkeypatch):
    module = _load_session_module(monkeypatch)

    monkeypatch.setattr(module, "Response", _StubResponse)

    async def _agent_stream(*_args, **_kwargs):
        yield "data:not-json"
        yield "data:" + json.dumps(
            {
                "event": "node_finished",
                "data": {"component_id": "c1", "outputs": {"structured": {"alpha": 1}}},
            }
        )
        yield "data:" + json.dumps(
            {
                "event": "node_finished",
                "data": {"component_id": "c2", "outputs": {"structured": {}}},
            }
        )
        yield "data:" + json.dumps({"event": "other", "data": {}})
        yield "data:" + json.dumps({"event": "message", "data": {"content": "hello"}})

    monkeypatch.setattr(module, "agent_completion", _agent_stream)
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"stream": True, "return_trace": True}))

    resp = _run(inspect.unwrap(module.agent_completions)("tenant-1", "agent-1"))
    chunks = _run(_collect_stream(resp.body))
    assert resp.headers.get("Content-Type") == "text/event-stream; charset=utf-8"
    assert any('"trace"' in chunk for chunk in chunks)
    assert any("hello" in chunk for chunk in chunks)
    assert chunks[-1].strip() == "data:[DONE]"

    async def _agent_nonstream(*_args, **_kwargs):
        yield "data:" + json.dumps({"event": "message", "data": {"content": "A", "reference": {"doc": "r"}}})
        yield "data:" + json.dumps(
            {
                "event": "node_finished",
                "data": {"component_id": "c2", "outputs": {"structured": {"foo": "bar"}}},
            }
        )
        yield "data:" + json.dumps(
            {
                "event": "node_finished",
                "data": {"component_id": "c3", "outputs": {"structured": {"baz": 1}}},
            }
        )
        yield "data:" + json.dumps(
            {
                "event": "node_finished",
                "data": {"component_id": "c4", "outputs": {"structured": {}}},
            }
        )

    monkeypatch.setattr(module, "agent_completion", _agent_nonstream)
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"stream": False, "return_trace": True}))
    res = _run(inspect.unwrap(module.agent_completions)("tenant-1", "agent-1"))
    assert res["data"]["data"]["content"] == "A"
    assert res["data"]["data"]["reference"] == {"doc": "r"}
    assert res["data"]["data"]["structured"] == {
        "c2": {"foo": "bar"},
        "c3": {"baz": 1},
        "c4": {},
    }
    assert [item["component_id"] for item in res["data"]["data"]["trace"]] == ["c2", "c3", "c4"]

    async def _agent_nonstream_broken(*_args, **_kwargs):
        yield "data:{"

    monkeypatch.setattr(module, "agent_completion", _agent_nonstream_broken)
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"stream": False, "return_trace": False}))
    res = _run(inspect.unwrap(module.agent_completions)("tenant-1", "agent-1"))
    assert res["data"].startswith("**ERROR**")