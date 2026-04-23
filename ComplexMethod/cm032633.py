def test_oauth_client_sync_matrix_unit(monkeypatch):
    oauth_module = _load_oauth_module(monkeypatch)
    client = oauth_module.OAuthClient(_base_config())

    assert client.client_id == "client-1"
    assert client.client_secret == "secret-1"
    assert client.authorization_url.endswith("/authorize")
    assert client.token_url.endswith("/token")
    assert client.userinfo_url.endswith("/userinfo")
    assert client.redirect_uri.endswith("/callback")
    assert client.scope == "openid profile"
    assert client.http_request_timeout == 7

    info = oauth_module.UserInfo("u@example.com", "user1", "User One", "avatar-url")
    assert info.to_dict() == {
        "email": "u@example.com",
        "username": "user1",
        "nickname": "User One",
        "avatar_url": "avatar-url",
    }

    auth_url = client.get_authorization_url(state="s p/a?ce")
    parsed = urllib.parse.urlparse(auth_url)
    query = urllib.parse.parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert query["client_id"] == ["client-1"]
    assert query["redirect_uri"] == ["https://app.example/callback"]
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["openid profile"]
    assert query["state"] == ["s p/a?ce"]

    no_scope_client = oauth_module.OAuthClient(_base_config(scope=None))
    no_scope_query = urllib.parse.parse_qs(urllib.parse.urlparse(no_scope_client.get_authorization_url()).query)
    assert "scope" not in no_scope_query

    call_log = []

    def _sync_ok(method, url, data=None, headers=None, timeout=None):
        call_log.append((method, url, data, headers, timeout))
        if url.endswith("/token"):
            return _FakeResponse({"access_token": "token-1"})
        return _FakeResponse({"email": "user@example.com", "picture": "id-picture"})

    monkeypatch.setattr(oauth_module, "sync_request", _sync_ok)
    token = client.exchange_code_for_token("code-1")
    assert token["access_token"] == "token-1"
    user_info = client.fetch_user_info("access-1")
    assert isinstance(user_info, oauth_module.UserInfo)
    assert user_info.to_dict() == {
        "email": "user@example.com",
        "username": "user",
        "nickname": "user",
        "avatar_url": "id-picture",
    }
    assert call_log[0][0] == "POST"
    assert call_log[0][3]["Accept"] == "application/json"
    assert call_log[1][0] == "GET"
    assert call_log[1][3]["Authorization"] == "Bearer access-1"

    normalized = client.normalize_user_info(
        {"email": "fallback@example.com", "username": "fallback-user", "nickname": "fallback-nick", "avatar_url": "direct-avatar"}
    )
    assert normalized.to_dict()["avatar_url"] == "direct-avatar"

    monkeypatch.setattr(oauth_module, "sync_request", lambda *_args, **_kwargs: _FakeResponse(err=RuntimeError("status boom")))
    with pytest.raises(ValueError, match="Failed to exchange authorization code for token: status boom"):
        client.exchange_code_for_token("code-2")
    with pytest.raises(ValueError, match="Failed to fetch user info: status boom"):
        client.fetch_user_info("access-2")