def test_searchbots_ask_embedded_auth_and_stream_unit(monkeypatch):
    module = _load_session_module(monkeypatch)
    monkeypatch.setattr(module, "Response", _StubResponse)

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer"}))
    res = _run(inspect.unwrap(module.ask_about_embedded)())
    assert res["message"] == "Authorization is not valid!"

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer bad"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [])
    res = _run(inspect.unwrap(module.ask_about_embedded)())
    assert "API key is invalid" in res["message"]

    monkeypatch.setattr(module, "request", SimpleNamespace(headers={"Authorization": "Bearer ok"}))
    monkeypatch.setattr(module.APIToken, "query", lambda **_kwargs: [SimpleNamespace(tenant_id="tenant-1")])
    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"question": "embedded q", "kb_ids": ["kb-1"], "search_id": "search-1"}),
    )
    monkeypatch.setattr(module.SearchService, "get_detail", lambda _search_id: {"search_config": {"mode": "test"}})
    captured = {}

    async def _embedded_async_ask(question, kb_ids, uid, search_config=None):
        captured["question"] = question
        captured["kb_ids"] = kb_ids
        captured["uid"] = uid
        captured["search_config"] = search_config
        yield {"answer": "embedded-answer"}
        raise RuntimeError("embedded stream boom")

    monkeypatch.setattr(module, "async_ask", _embedded_async_ask)
    resp = _run(inspect.unwrap(module.ask_about_embedded)())
    assert isinstance(resp, _StubResponse)
    assert resp.headers.get("Content-Type") == "text/event-stream; charset=utf-8"
    chunks = _run(_collect_stream(resp.body))
    assert any('"answer": "embedded-answer"' in chunk for chunk in chunks)
    assert any('"code": 500' in chunk and "**ERROR**: embedded stream boom" in chunk for chunk in chunks)
    assert '"data": true' in chunks[-1].lower()
    assert captured["search_config"] == {"mode": "test"}