def test_chat_session_delete_routes_partial_duplicate_unit(monkeypatch):
    module = _load_chat_module(monkeypatch)

    monkeypatch.setattr(module.DialogService, "query", lambda **_kwargs: [SimpleNamespace(id="chat-1")])
    _set_request_json(monkeypatch, module, {})
    res = _run(module.delete_sessions.__wrapped__("chat-1"))
    assert res["code"] == 0

    monkeypatch.setattr(module.ConversationService, "delete_by_id", lambda *_args, **_kwargs: True)

    def _conversation_query(**kwargs):
        if "dialog_id" in kwargs and "id" not in kwargs:
            return [SimpleNamespace(id="seed")]
        if kwargs.get("id") == "ok":
            return [SimpleNamespace(id="ok")]
        return []

    monkeypatch.setattr(module.ConversationService, "query", _conversation_query)

    _set_request_json(monkeypatch, module, {"ids": ["ok", "bad"]})
    monkeypatch.setattr(module, "check_duplicate_ids", lambda ids, _kind: (ids, []))
    res = _run(module.delete_sessions.__wrapped__("chat-1"))
    assert res["code"] == 0
    assert res["data"]["success_count"] == 1
    assert res["data"]["errors"] == ["The chat doesn't own the session bad"]

    _set_request_json(monkeypatch, module, {"ids": ["bad"]})
    monkeypatch.setattr(module, "check_duplicate_ids", lambda ids, _kind: (ids, []))
    res = _run(module.delete_sessions.__wrapped__("chat-1"))
    assert res["message"] == "The chat doesn't own the session bad"

    _set_request_json(monkeypatch, module, {"ids": ["ok", "ok"]})
    monkeypatch.setattr(module, "check_duplicate_ids", lambda ids, _kind: (["ok"], ["Duplicate session ids: ok"]))
    res = _run(module.delete_sessions.__wrapped__("chat-1"))
    assert res["code"] == 0
    assert res["data"]["success_count"] == 1
    assert res["data"]["errors"] == ["Duplicate session ids: ok"]