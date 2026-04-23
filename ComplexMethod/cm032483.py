def test_chat_list_sessions_forwards_restful_query_params(monkeypatch):
    client = RAGFlow("token", "http://localhost:9380")
    chat = Chat(client, {"id": "chat-1"})
    calls = []

    def _ok_get(path, params=None):
        calls.append((path, params))
        return _DummyResponse(
            {
                "code": 0,
                "data": [
                    {"id": "session-1", "chat_id": "chat-1", "name": "one"},
                    {"id": "session-2", "chat_id": "chat-1", "name": "two"},
                ],
            }
        )

    monkeypatch.setattr(chat, "get", _ok_get)

    sessions = chat.list_sessions(page=2, page_size=2, orderby="create_time", desc=False, id="session-1", name="one", user_id="user-1")
    assert len(sessions) == 2, str(sessions)
    assert all(isinstance(item, Session) for item in sessions), str(sessions)
    assert calls[-1][0] == "/chats/chat-1/sessions"
    assert calls[-1][1]["page_size"] == 2
    assert calls[-1][1]["name"] == "one"
    assert calls[-1][1]["user_id"] == "user-1"

    all_sessions = chat.list_sessions(page_size=0)
    assert len(all_sessions) == 2, str(all_sessions)
    assert calls[-1][1]["page_size"] == 0