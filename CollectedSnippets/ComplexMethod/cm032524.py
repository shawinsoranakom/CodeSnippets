def test_chat_session_create_and_update_guard_matrix_unit(monkeypatch):
    module = _load_chat_module(monkeypatch)

    _set_request_json(monkeypatch, module, {"name": "session"})
    monkeypatch.setattr(module.DialogService, "query", lambda **_kwargs: [])
    res = _run(module.create_session.__wrapped__("chat-1"))
    assert res["message"] == "No authorization."

    dia = SimpleNamespace(prompt_config={"prologue": "hello"})
    monkeypatch.setattr(module.DialogService, "query", lambda **_kwargs: [dia])
    monkeypatch.setattr(module.DialogService, "get_by_id", lambda _id: (True, dia))
    monkeypatch.setattr(module.ConversationService, "save", lambda **_kwargs: None)
    monkeypatch.setattr(module.ConversationService, "get_by_id", lambda _id: (False, None))
    res = _run(module.create_session.__wrapped__("chat-1"))
    assert "Fail to create a session" in res["message"]

    _set_request_json(monkeypatch, module, {})
    monkeypatch.setattr(module.ConversationService, "query", lambda **_kwargs: [])
    res = _run(module.update_session.__wrapped__("chat-1", "session-1"))
    assert res["message"] == "Session not found!"

    monkeypatch.setattr(module.ConversationService, "query", lambda **_kwargs: [SimpleNamespace(id="session-1")])
    monkeypatch.setattr(module.DialogService, "query", lambda **_kwargs: [])
    res = _run(module.update_session.__wrapped__("chat-1", "session-1"))
    assert res["message"] == "No authorization."

    monkeypatch.setattr(module.DialogService, "query", lambda **_kwargs: [SimpleNamespace(id="chat-1")])
    _set_request_json(monkeypatch, module, {"message": []})
    res = _run(module.update_session.__wrapped__("chat-1", "session-1"))
    assert "`messages` cannot be changed." in res["message"]

    _set_request_json(monkeypatch, module, {"reference": []})
    res = _run(module.update_session.__wrapped__("chat-1", "session-1"))
    assert "`reference` cannot be changed." in res["message"]

    _set_request_json(monkeypatch, module, {"name": ""})
    res = _run(module.update_session.__wrapped__("chat-1", "session-1"))
    assert "`name` can not be empty." in res["message"]

    _set_request_json(monkeypatch, module, {"name": "renamed"})
    monkeypatch.setattr(module.ConversationService, "update_by_id", lambda *_args, **_kwargs: False)
    res = _run(module.update_session.__wrapped__("chat-1", "session-1"))
    assert res["message"] == "Session not found!"