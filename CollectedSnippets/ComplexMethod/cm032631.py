def test_google_web_oauth_callbacks_matrix(monkeypatch):
    module = _load_connector_app(monkeypatch)

    flow_calls = []

    def _from_client_config(client_config, scopes):
        flow = _FakeFlow(client_config, scopes)
        flow_calls.append(flow)
        return flow

    monkeypatch.setattr(module.Flow, "from_client_config", staticmethod(_from_client_config))

    callback_specs = [
        (
            module.google_gmail_web_oauth_callback,
            "gmail",
            module.GMAIL_WEB_OAUTH_REDIRECT_URI,
            module.GOOGLE_SCOPES[module.DocumentSource.GMAIL],
        ),
        (
            module.google_drive_web_oauth_callback,
            "google-drive",
            module.GOOGLE_DRIVE_WEB_OAUTH_REDIRECT_URI,
            module.GOOGLE_SCOPES[module.DocumentSource.GOOGLE_DRIVE],
        ),
    ]

    for callback, source, expected_redirect, expected_scopes in callback_specs:
        redis = _FakeRedis()
        monkeypatch.setattr(module, "REDIS_CONN", redis)

        _set_request(module, args={})
        missing_state = _run(callback())
        assert "Missing OAuth state parameter." in missing_state.body

        _set_request(module, args={"state": "sid"})
        expired_state = _run(callback())
        assert "Authorization session expired" in expired_state.body

        redis.store[module._web_state_cache_key("sid", source)] = json.dumps({"user_id": "tenant-1"})
        _set_request(module, args={"state": "sid"})
        invalid_state = _run(callback())
        assert "Authorization session was invalid" in invalid_state.body
        assert module._web_state_cache_key("sid", source) in redis.deleted

        redis.store[module._web_state_cache_key("sid", source)] = json.dumps({
            "user_id": "tenant-1",
            "client_config": {"web": {"client_id": "cid"}},
        })
        _set_request(module, args={"state": "sid", "error": "denied", "error_description": "permission denied"})
        oauth_error = _run(callback())
        assert "permission denied" in oauth_error.body

        redis.store[module._web_state_cache_key("sid", source)] = json.dumps({
            "user_id": "tenant-1",
            "client_config": {"web": {"client_id": "cid"}},
        })
        _set_request(module, args={"state": "sid"})
        missing_code = _run(callback())
        assert "Missing authorization code" in missing_code.body

        redis.store[module._web_state_cache_key("sid", source)] = json.dumps({
            "user_id": "tenant-1",
            "client_config": {"web": {"client_id": "cid"}},
        })
        _set_request(module, args={"state": "sid", "code": "code-123"})
        success = _run(callback())
        assert "Authorization completed successfully." in success.body

        result_key = module._web_result_cache_key("sid", source)
        assert result_key in redis.store
        assert module._web_state_cache_key("sid", source) in redis.deleted

        assert flow_calls[-1].redirect_uri == expected_redirect
        assert flow_calls[-1].scopes == expected_scopes
        assert flow_calls[-1].token_code == "code-123"