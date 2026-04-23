def test_session_module_streaming_and_helper_paths_unit(monkeypatch):
    client = RAGFlow("token", "http://localhost:9380")
    chat_session = Session(client, {"id": "session-chat", "chat_id": "chat-1"})
    chat_done_session = Session(client, {"id": "session-chat-done", "chat_id": "chat-1"})
    agent_session = Session(client, {"id": "session-agent", "agent_id": "agent-1"})
    calls = []

    chat_stream = _DummyStreamResponse(
        [
            "",
            "data: {bad json}",
            'data: {"event":"workflow_started","data":{"content":"skip"}}',
            '{"data":{"answer":"chat-answer","reference":{"chunks":[{"id":"chunk-1"}]}}}',
            'data: {"data": true}',
            "data: [DONE]",
        ]
    )
    agent_stream = _DummyStreamResponse(
        [
            "data: {bad json}",
            'data: {"event":"message","data":{"content":"agent-answer"}}',
            'data: {"event":"message_end","data":{"content":"done"}}',
        ]
    )

    def _chat_post(path, json=None, stream=False, files=None):
        calls.append(("chat", path, json, stream, files))
        return chat_stream

    def _agent_post(path, json=None, stream=False, files=None):
        calls.append(("agent", path, json, stream, files))
        return agent_stream

    monkeypatch.setattr(chat_session, "post", _chat_post)
    monkeypatch.setattr(
        chat_done_session,
        "post",
        lambda *_args, **_kwargs: _DummyStreamResponse(
            ['{"data":{"answer":"chat-done","reference":{"chunks":[]}}}', "data: [DONE]"]
        ),
    )
    monkeypatch.setattr(agent_session, "post", _agent_post)

    chat_messages = list(chat_session.ask("hello chat", stream=True, temperature=0.2))
    assert len(chat_messages) == 1
    assert chat_messages[0].content == "chat-answer"
    assert chat_messages[0].reference == [{"id": "chunk-1"}]

    chat_done_messages = list(chat_done_session.ask("hello done", stream=True))
    assert len(chat_done_messages) == 1
    assert chat_done_messages[0].content == "chat-done"

    agent_messages = list(agent_session.ask("hello agent", stream=True, top_p=0.8))
    assert len(agent_messages) == 1
    assert agent_messages[0].content == "agent-answer"

    assert calls[0][1] == "/chats/chat-1/completions"
    assert calls[0][2]["question"] == "hello chat"
    assert calls[0][2]["session_id"] == "session-chat"
    assert calls[0][2]["temperature"] == 0.2
    assert calls[0][3] is True
    assert calls[1][1] == "/agents/agent-1/completions"
    assert calls[1][2]["question"] == "hello agent"
    assert calls[1][2]["session_id"] == "session-agent"
    assert calls[1][2]["top_p"] == 0.8
    assert calls[1][3] is True