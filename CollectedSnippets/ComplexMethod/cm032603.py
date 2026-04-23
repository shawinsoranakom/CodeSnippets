def test_webhook_background_run_success_and_error_trace_paths(monkeypatch):
    module = _load_agents_app(monkeypatch)

    redis_store = {}

    def redis_get(key):
        return redis_store.get(key)

    def redis_set_obj(key, obj, _ttl):
        redis_store[key] = json.dumps(obj)

    monkeypatch.setattr(module.REDIS_CONN, "get", redis_get)
    monkeypatch.setattr(module.REDIS_CONN, "set_obj", redis_set_obj)

    update_calls = []
    monkeypatch.setattr(module.UserCanvasService, "update_by_id", lambda *_args, **_kwargs: update_calls.append(True))

    tasks = []

    def _capture_task(coro):
        tasks.append(coro)
        return SimpleNamespace()

    monkeypatch.setattr(module.asyncio, "create_task", _capture_task)

    class _CanvasSuccess(_StubCanvas):
        async def run(self, **_kwargs):
            yield {"event": "message", "data": {"content": "ok"}}

        def __str__(self):
            return "{}"

    monkeypatch.setattr(module, "Canvas", _CanvasSuccess)

    params = _default_webhook_params(security={"auth_type": "none"}, content_types="application/json")
    cvs = _make_webhook_cvs(module, params=params)
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id: (True, cvs))
    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(path="/api/v1/webhook_test/agent-1", headers={"Content-Type": "application/json"}, json_body={}),
    )

    res = _run(module.webhook("agent-1"))
    assert res.status_code == 200
    assert len(tasks) == 1
    _run(tasks.pop(0))
    assert update_calls == [True]

    key = "webhook-trace-agent-1-logs"
    trace_obj = json.loads(redis_store[key])
    ws = next(iter(trace_obj["webhooks"].values()))
    events = ws["events"]
    assert any(event.get("event") == "message" for event in events)
    assert any(event.get("event") == "finished" and event.get("success") is True for event in events)

    class _CanvasError(_StubCanvas):
        async def run(self, **_kwargs):
            raise RuntimeError("run failed")
            yield {}

    monkeypatch.setattr(module, "Canvas", _CanvasError)
    tasks.clear()
    redis_store.clear()
    cvs = _make_webhook_cvs(module, params=params)
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id, _cvs=cvs: (True, _cvs))
    res = _run(module.webhook("agent-1"))
    assert res.status_code == 200
    _run(tasks.pop(0))
    trace_obj = json.loads(redis_store[key])
    ws = next(iter(trace_obj["webhooks"].values()))
    events = ws["events"]
    assert any(event.get("event") == "error" for event in events)
    assert any(event.get("event") == "finished" and event.get("success") is False for event in events)

    log_messages = []
    monkeypatch.setattr(module.logging, "exception", lambda msg, *_args, **_kwargs: log_messages.append(str(msg)))
    monkeypatch.setattr(module.REDIS_CONN, "get", lambda _key: "{")
    monkeypatch.setattr(module.REDIS_CONN, "set_obj", lambda *_args, **_kwargs: None)
    tasks.clear()
    cvs = _make_webhook_cvs(module, params=params)
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id, _cvs=cvs: (True, _cvs))
    _run(module.webhook("agent-1"))
    _run(tasks.pop(0))
    assert any("Failed to append webhook trace" in msg for msg in log_messages)