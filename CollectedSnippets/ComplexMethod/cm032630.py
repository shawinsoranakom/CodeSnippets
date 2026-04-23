def test_start_google_web_oauth_matrix(monkeypatch):
    module = _load_connector_app(monkeypatch)

    redis = _FakeRedis()
    monkeypatch.setattr(module, "REDIS_CONN", redis)
    monkeypatch.setattr(module.time, "time", lambda: 1700000000)

    flow_calls = []

    def _from_client_config(client_config, scopes):
        flow = _FakeFlow(client_config, scopes)
        flow_calls.append(flow)
        return flow

    monkeypatch.setattr(module.Flow, "from_client_config", staticmethod(_from_client_config))

    _set_request(module, args={"type": "invalid"})
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"credentials": "{}"}))
    invalid_type = _run(module.start_google_web_oauth())
    assert invalid_type["code"] == module.RetCode.ARGUMENT_ERROR

    monkeypatch.setattr(module, "GMAIL_WEB_OAUTH_REDIRECT_URI", "")
    _set_request(module, args={"type": "gmail"})
    missing_redirect = _run(module.start_google_web_oauth())
    assert missing_redirect["code"] == module.RetCode.SERVER_ERROR

    monkeypatch.setattr(module, "GMAIL_WEB_OAUTH_REDIRECT_URI", "https://example.com/gmail")
    monkeypatch.setattr(module, "GOOGLE_DRIVE_WEB_OAUTH_REDIRECT_URI", "https://example.com/drive")

    _set_request(module, args={"type": "google-drive"})
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"credentials": "{invalid-json"}))
    invalid_credentials = _run(module.start_google_web_oauth())
    assert invalid_credentials["code"] == module.RetCode.ARGUMENT_ERROR

    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"credentials": json.dumps({"web": {"client_id": "id"}, "refresh_token": "rt"})}),
    )
    has_refresh_token = _run(module.start_google_web_oauth())
    assert has_refresh_token["code"] == module.RetCode.ARGUMENT_ERROR

    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"credentials": json.dumps({"installed": {"x": 1}})}))
    missing_web = _run(module.start_google_web_oauth())
    assert missing_web["code"] == module.RetCode.ARGUMENT_ERROR

    ids = iter(["flow-gmail", "flow-drive"])
    monkeypatch.setattr(module.uuid, "uuid4", lambda: next(ids))

    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"credentials": json.dumps({"web": {"client_id": "id", "client_secret": "secret"}})}),
    )

    _set_request(module, args={"type": "gmail"})
    gmail_ok = _run(module.start_google_web_oauth())
    assert gmail_ok["code"] == 0
    assert gmail_ok["data"]["flow_id"] == "flow-gmail"
    assert gmail_ok["data"]["authorization_url"].endswith("flow-gmail")

    _set_request(module, args={})
    drive_ok = _run(module.start_google_web_oauth())
    assert drive_ok["code"] == 0
    assert drive_ok["data"]["flow_id"] == "flow-drive"
    assert drive_ok["data"]["authorization_url"].endswith("flow-drive")

    assert any(call.scopes == module.GOOGLE_SCOPES[module.DocumentSource.GMAIL] for call in flow_calls)
    assert any(call.scopes == module.GOOGLE_SCOPES[module.DocumentSource.GOOGLE_DRIVE] for call in flow_calls)
    assert "gmail_web_flow_state:flow-gmail" in redis.store
    assert "google-drive_web_flow_state:flow-drive" in redis.store