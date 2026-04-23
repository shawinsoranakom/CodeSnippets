def test_sessions_ask_route_validation_and_stream_unit(monkeypatch):
    module = _load_session_module(monkeypatch)
    monkeypatch.setattr(module, "Response", _StubResponse)

    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"dataset_ids": ["kb-1"]}))
    res = _run(inspect.unwrap(module.ask_about)("tenant-1"))
    assert res["message"] == "`question` is required."

    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"question": "q"}))
    res = _run(inspect.unwrap(module.ask_about)("tenant-1"))
    assert res["message"] == "`dataset_ids` is required."

    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"question": "q", "dataset_ids": "kb-1"}))
    res = _run(inspect.unwrap(module.ask_about)("tenant-1"))
    assert res["message"] == "`dataset_ids` should be a list."

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"question": "q", "dataset_ids": ["kb-1"]}))
    res = _run(inspect.unwrap(module.ask_about)("tenant-1"))
    assert res["message"] == "You don't own the dataset kb-1."

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: [SimpleNamespace(chunk_num=0)])
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"question": "q", "dataset_ids": ["kb-1"]}))
    res = _run(inspect.unwrap(module.ask_about)("tenant-1"))
    assert res["message"] == "The dataset kb-1 doesn't own parsed file"

    monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: [SimpleNamespace(chunk_num=1)])
    captured = {}

    async def _streaming_async_ask(question, kb_ids, uid):
        captured["question"] = question
        captured["kb_ids"] = kb_ids
        captured["uid"] = uid
        yield {"answer": "first"}
        raise RuntimeError("ask stream boom")

    monkeypatch.setattr(module, "async_ask", _streaming_async_ask)
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"question": "q", "dataset_ids": ["kb-1"]}))
    resp = _run(inspect.unwrap(module.ask_about)("tenant-1"))
    assert isinstance(resp, _StubResponse)
    assert resp.headers.get("Content-Type") == "text/event-stream; charset=utf-8"
    chunks = _run(_collect_stream(resp.body))
    assert any('"answer": "first"' in chunk for chunk in chunks)
    assert any('"code": 500' in chunk and "**ERROR**: ask stream boom" in chunk for chunk in chunks)
    assert '"data": true' in chunks[-1].lower()
    assert captured == {"question": "q", "kb_ids": ["kb-1"], "uid": "tenant-1"}