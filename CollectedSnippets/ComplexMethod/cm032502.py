def test_openai_stream_generator_branches_unit(monkeypatch):
    module = _load_session_module(monkeypatch)

    monkeypatch.setattr(module, "Response", _StubResponse)
    monkeypatch.setattr(module, "num_tokens_from_string", lambda text: len(text or ""))
    monkeypatch.setattr(module, "convert_conditions", lambda cond: cond.get("conditions", []))
    monkeypatch.setattr(module, "meta_filter", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(module.DocMetadataService, "get_flatted_meta_by_kbs", lambda _kb_ids: [{"id": "doc-1"}])
    monkeypatch.setattr(module.DialogService, "query", lambda **_kwargs: [SimpleNamespace(kb_ids=["kb-1"])])
    monkeypatch.setattr(module, "_build_reference_chunks", lambda *_args, **_kwargs: [{"id": "ref-1"}])

    async def fake_async_chat(_dia, _msg, _stream, **_kwargs):
        yield {"start_to_think": True}
        yield {"answer": "R"}
        yield {"end_to_think": True}
        yield {"answer": ""}
        yield {"answer": "C"}
        yield {"final": True, "answer": "DONE", "reference": {"chunks": []}}
        raise RuntimeError("boom")

    monkeypatch.setattr(module, "async_chat", fake_async_chat)

    payload = {
        "model": "model",
        "stream": True,
        "messages": [
            {"role": "system", "content": "sys"},
            {"role": "assistant", "content": "preface"},
            {"role": "user", "content": "hello"},
        ],
        "extra_body": {
            "reference": True,
            "reference_metadata": {"include": True, "fields": ["author"]},
            "metadata_condition": {"logic": "and", "conditions": [{"name": "author", "value": "bob"}]},
        },
    }
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue(payload))

    resp = _run(inspect.unwrap(module.chat_completion_openai_like)("tenant-1", "chat-1"))
    assert isinstance(resp, _StubResponse)
    assert resp.headers.get("Content-Type") == "text/event-stream; charset=utf-8"

    chunks = _run(_collect_stream(resp.body))
    assert any("reasoning_content" in chunk for chunk in chunks)
    assert any("**ERROR**: boom" in chunk for chunk in chunks)
    assert any('"usage"' in chunk for chunk in chunks)
    assert any('"reference"' in chunk for chunk in chunks)
    assert chunks[-1].strip() == "data:[DONE]"