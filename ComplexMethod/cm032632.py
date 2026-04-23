def test_box_oauth_start_callback_and_poll_matrix(monkeypatch):
    module = _load_connector_app(monkeypatch)
    redis = _FakeRedis()
    monkeypatch.setattr(module, "REDIS_CONN", redis)

    created_auth = []

    class _TrackingBoxOAuth(_FakeBoxOAuth):
        def __init__(self, config):
            super().__init__(config)
            created_auth.append(self)

    monkeypatch.setattr(module, "BoxOAuth", _TrackingBoxOAuth)
    monkeypatch.setattr(module.uuid, "uuid4", lambda: "flow-box")
    monkeypatch.setattr(module.time, "time", lambda: 1800000000)

    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({}))
    missing_params = _run(module.start_box_web_oauth())
    assert missing_params["code"] == module.RetCode.ARGUMENT_ERROR

    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"client_id": "cid", "client_secret": "sec", "redirect_uri": "https://box.local/callback"}),
    )
    start_ok = _run(module.start_box_web_oauth())
    assert start_ok["code"] == 0
    assert start_ok["data"]["flow_id"] == "flow-box"
    assert "authorization_url" in start_ok["data"]
    assert module._web_state_cache_key("flow-box", "box") in redis.store

    _set_request(module, args={})
    missing_state = _run(module.box_web_oauth_callback())
    assert "Missing OAuth parameters." in missing_state.body

    _set_request(module, args={"state": "flow-box"})
    missing_code = _run(module.box_web_oauth_callback())
    assert "Missing authorization code from Box." in missing_code.body

    redis.store[module._web_state_cache_key("flow-null", "box")] = "null"
    _set_request(module, args={"state": "flow-null", "code": "abc"})
    invalid_session = _run(module.box_web_oauth_callback())
    assert invalid_session["code"] == module.RetCode.ARGUMENT_ERROR

    redis.store[module._web_state_cache_key("flow-box", "box")] = json.dumps(
        {"user_id": "tenant-1", "client_id": "cid", "client_secret": "sec"}
    )
    _set_request(module, args={"state": "flow-box", "code": "abc", "error": "access_denied", "error_description": "denied"})
    callback_error = _run(module.box_web_oauth_callback())
    assert "denied" in callback_error.body

    redis.store[module._web_state_cache_key("flow-ok", "box")] = json.dumps(
        {"user_id": "tenant-1", "client_id": "cid", "client_secret": "sec"}
    )
    _set_request(module, args={"state": "flow-ok", "code": "code-ok"})
    callback_success = _run(module.box_web_oauth_callback())
    assert "Authorization completed successfully." in callback_success.body
    assert created_auth[-1].exchange_code == "code-ok"
    assert module._web_result_cache_key("flow-ok", "box") in redis.store
    assert module._web_state_cache_key("flow-ok", "box") in redis.deleted

    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"flow_id": "flow-ok"}))
    redis.store.pop(module._web_result_cache_key("flow-ok", "box"), None)
    pending = _run(module.poll_box_web_result())
    assert pending["code"] == module.RetCode.RUNNING

    redis.store[module._web_result_cache_key("flow-ok", "box")] = json.dumps({"user_id": "another-user"})
    permission_error = _run(module.poll_box_web_result())
    assert permission_error["code"] == module.RetCode.PERMISSION_ERROR

    redis.store[module._web_result_cache_key("flow-ok", "box")] = json.dumps(
        {"user_id": "tenant-1", "access_token": "at", "refresh_token": "rt"}
    )
    poll_success = _run(module.poll_box_web_result())
    assert poll_success["code"] == 0
    assert poll_success["data"]["credentials"]["access_token"] == "at"
    assert module._web_result_cache_key("flow-ok", "box") in redis.deleted