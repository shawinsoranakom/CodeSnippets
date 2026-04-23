def test_webhook_trace_polling_branches(monkeypatch):
    module = _load_agents_app(monkeypatch)

    # Missing since_ts.
    monkeypatch.setattr(module, "request", SimpleNamespace(args=_Args()))
    res = _run(module.webhook_trace("agent-1"))
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["webhook_id"] is None
    assert res["data"]["events"] == []
    assert res["data"]["finished"] is False

    # since_ts provided but no Redis data.
    monkeypatch.setattr(module, "request", SimpleNamespace(args=_Args({"since_ts": "100.0"})))
    monkeypatch.setattr(module.REDIS_CONN, "get", lambda _k: None)
    res = _run(module.webhook_trace("agent-1"))
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["webhook_id"] is None
    assert res["data"]["next_since_ts"] == 100.0
    assert res["data"]["events"] == []
    assert res["data"]["finished"] is False

    webhooks_obj = {
        "webhooks": {
            "101.0": {
                "events": [
                    {"event": "message", "ts": 101.2, "data": {"content": "a"}},
                    {"event": "finished", "ts": 102.5},
                ]
            },
            "99.0": {"events": [{"event": "message", "ts": 99.1}]},
        }
    }
    raw = json.dumps(webhooks_obj)
    monkeypatch.setattr(module.REDIS_CONN, "get", lambda _k: raw)

    # No candidates newer than since_ts.
    monkeypatch.setattr(module, "request", SimpleNamespace(args=_Args({"since_ts": "200.0"})))
    res = _run(module.webhook_trace("agent-1"))
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["webhook_id"] is None
    assert res["data"]["next_since_ts"] == 200.0
    assert res["data"]["events"] == []
    assert res["data"]["finished"] is False

    # Candidate exists and webhook id is assigned.
    monkeypatch.setattr(module, "request", SimpleNamespace(args=_Args({"since_ts": "100.0"})))
    res = _run(module.webhook_trace("agent-1"))
    assert res["code"] == module.RetCode.SUCCESS
    webhook_id = res["data"]["webhook_id"]
    assert webhook_id
    assert res["data"]["events"] == []
    assert res["data"]["next_since_ts"] == 101.0
    assert res["data"]["finished"] is False

    # Invalid webhook id.
    monkeypatch.setattr(
        module,
        "request",
        SimpleNamespace(args=_Args({"since_ts": "100.0", "webhook_id": "bad-id"})),
    )
    res = _run(module.webhook_trace("agent-1"))
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["webhook_id"] == "bad-id"
    assert res["data"]["events"] == []
    assert res["data"]["next_since_ts"] == 100.0
    assert res["data"]["finished"] is True

    # Valid webhook id with event filtering and finished flag.
    monkeypatch.setattr(
        module,
        "request",
        SimpleNamespace(args=_Args({"since_ts": "101.0", "webhook_id": webhook_id})),
    )
    res = _run(module.webhook_trace("agent-1"))
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["webhook_id"] == webhook_id
    assert [event["ts"] for event in res["data"]["events"]] == [101.2, 102.5]
    assert res["data"]["next_since_ts"] == 102.5
    assert res["data"]["finished"] is True