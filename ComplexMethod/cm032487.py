def test_agent_session_methods_success_and_error_paths(monkeypatch):
    client = RAGFlow("token", "http://localhost:9380")
    agent = Agent(client, {"id": "agent-1"})
    calls = {"post": [], "get": [], "rm": []}

    def _ok_post(path, json=None, stream=False, files=None):
        calls["post"].append((path, json, stream, files))
        return _DummyResponse({"code": 0, "data": {"id": "session-1", "agent_id": "agent-1", "name": "one"}})

    def _ok_get(path, params=None):
        calls["get"].append((path, params))
        return _DummyResponse(
            {
                "code": 0,
                "data": [
                    {"id": "session-1", "agent_id": "agent-1", "name": "one"},
                    {"id": "session-2", "agent_id": "agent-1", "name": "two"},
                ],
            }
        )

    def _ok_rm(path, payload):
        calls["rm"].append((path, payload))
        return _DummyResponse({"code": 0, "message": "ok"})

    monkeypatch.setattr(agent, "post", _ok_post)
    monkeypatch.setattr(agent, "get", _ok_get)
    monkeypatch.setattr(agent, "rm", _ok_rm)

    session = agent.create_session(name="session-name")
    assert isinstance(session, Session), str(session)
    assert session.id == "session-1", str(session)
    assert calls["post"][-1][0] == "/agents/agent-1/sessions"
    assert calls["post"][-1][1] == {"name": "session-name"}

    sessions = agent.list_sessions(page=2, page_size=5, orderby="create_time", desc=False, id="session-1")
    assert len(sessions) == 2, str(sessions)
    assert all(isinstance(item, Session) for item in sessions), str(sessions)
    assert calls["get"][-1][0] == "/agents/agent-1/sessions"
    assert calls["get"][-1][1]["page"] == 2
    assert calls["get"][-1][1]["id"] == "session-1"

    agent.delete_sessions(ids=["session-1", "session-2"])
    assert calls["rm"][-1] == ("/agents/agent-1/sessions", {"ids": ["session-1", "session-2"]})

    monkeypatch.setattr(agent, "post", lambda *_args, **_kwargs: _DummyResponse({"code": 1, "message": "create failed"}))
    with pytest.raises(Exception, match="create failed"):
        agent.create_session(name="bad")

    monkeypatch.setattr(agent, "get", lambda *_args, **_kwargs: _DummyResponse({"code": 2, "message": "list failed"}))
    with pytest.raises(Exception, match="list failed"):
        agent.list_sessions()

    monkeypatch.setattr(agent, "rm", lambda *_args, **_kwargs: _DummyResponse({"code": 3, "message": "delete failed"}))
    with pytest.raises(Exception, match="delete failed"):
        agent.delete_sessions(ids=["session-1"])