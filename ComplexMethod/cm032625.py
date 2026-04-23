def test_trace_and_sessions_matrix_unit(monkeypatch):
    module = _load_canvas_module(monkeypatch)

    monkeypatch.setattr(module, "request", _DummyRequest(args=_Args({"canvas_id": "c1", "message_id": "m1"})))
    monkeypatch.setattr(module.REDIS_CONN, "get", lambda _key: None)
    res = module.trace()
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"] == {}

    monkeypatch.setattr(module.REDIS_CONN, "get", lambda _key: '{"event":"ok"}')
    res = module.trace()
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"] == {"event": "ok"}

    monkeypatch.setattr(module.REDIS_CONN, "get", lambda _key: (_ for _ in ()).throw(RuntimeError("trace boom")))
    res = module.trace()
    assert res is None

    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(module, "request", _DummyRequest(args=_Args({})))
    res = module.sessions("canvas-1")
    assert res["code"] == module.RetCode.OPERATING_ERROR

    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module, "request", _DummyRequest(args=_Args({"desc": "false", "exp_user_id": "exp-1"})))
    monkeypatch.setattr(module.API4ConversationService, "get_names", lambda _canvas_id, _exp_user_id: [{"id": "s1"}, {"id": "s2"}])
    res = module.sessions("canvas-1")
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["total"] == 2

    list_calls = []

    def _get_list(*args, **kwargs):
        list_calls.append((args, kwargs))
        return 7, [{"id": "s3"}]

    monkeypatch.setattr(module.API4ConversationService, "get_list", _get_list)
    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(args=_Args({"page": "3", "page_size": "9", "orderby": "update_time", "dsl": "false"})),
    )
    res = module.sessions("canvas-1")
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["total"] == 7
    assert list_calls[-1][0][4] == "update_time"
    assert list_calls[-1][0][5] is True
    assert list_calls[-1][0][8] is False

    monkeypatch.setattr(module, "get_json_result", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("result boom")))
    res = module.sessions("canvas-1")
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "result boom" in res["message"]