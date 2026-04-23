def test_session_module_error_paths_unit(monkeypatch):
    client = RAGFlow("token", "http://localhost:9380")

    unknown_session = Session(client, {"id": "session-unknown", "chat_id": "chat-1"})
    unknown_session._Session__session_type = "unknown"  # noqa: SLF001
    with pytest.raises(Exception) as exception_info:
        list(unknown_session.ask("hello", stream=False))
    assert "Unknown session type" in str(exception_info.value)

    bad_json_session = Session(client, {"id": "session-bad-json", "chat_id": "chat-1"})

    class _BadJsonResponse:
        def json(self):
            raise ValueError("json decode failed")

    monkeypatch.setattr(bad_json_session, "post", lambda *_args, **_kwargs: _BadJsonResponse())
    with pytest.raises(Exception) as exception_info:
        list(bad_json_session.ask("hello", stream=False))
    assert "Invalid response" in str(exception_info.value)

    ok_json_session = Session(client, {"id": "session-ok-json", "chat_id": "chat-1"})

    class _OkJsonResponse:
        def json(self):
            return {"data": {"answer": "ok-answer", "reference": {"chunks": [{"id": "chunk-ok"}]}}}

    monkeypatch.setattr(ok_json_session, "post", lambda *_args, **_kwargs: _OkJsonResponse())
    ok_messages = list(ok_json_session.ask("hello", stream=False))
    assert len(ok_messages) == 1
    assert ok_messages[0].content == "ok-answer"
    assert ok_messages[0].reference == [{"id": "chunk-ok"}]

    transport_session = Session(client, {"id": "session-transport", "chat_id": "chat-1"})
    monkeypatch.setattr(
        transport_session,
        "post",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("transport boom")),
    )
    with pytest.raises(RuntimeError) as exception_info:
        list(transport_session.ask("hello", stream=False))
    assert "transport boom" in str(exception_info.value)

    message = Message(client, {})
    assert message.content == "Hi! I am your assistant, can I help you?"
    assert message.reference is None
    assert message.role == "assistant"
    assert message.prompt is None
    assert message.id is None