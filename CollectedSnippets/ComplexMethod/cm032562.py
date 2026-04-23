def test_oauth_callback_matrix_unit(monkeypatch):
    module = _load_user_app(monkeypatch)
    module.settings.OAUTH_CONFIG = {"github": {"display_name": "GitHub", "icon": "gh"}}

    class _SyncAuthClient:
        def __init__(self, token_info, user_info):
            self._token_info = token_info
            self._user_info = user_info

        def exchange_code_for_token(self, _code):
            return self._token_info

        def fetch_user_info(self, _token, id_token=None):
            _ = id_token
            return self._user_info

    class _AsyncAuthClient:
        def __init__(self, token_info, user_info):
            self._token_info = token_info
            self._user_info = user_info

        async def async_exchange_code_for_token(self, _code):
            return self._token_info

        async def async_fetch_user_info(self, _token, id_token=None):
            _ = id_token
            return self._user_info

    _set_request_args(monkeypatch, module, {"state": "x", "code": "c"})
    module.session.clear()
    res = _run(module.oauth_callback("missing"))
    assert "Invalid channel name: missing" in res["redirect"]

    sync_ok = _SyncAuthClient(
        token_info={"access_token": "token-sync", "id_token": "id-sync"},
        user_info=SimpleNamespace(email="sync@example.com", avatar_url="http://img", nickname="sync"),
    )
    monkeypatch.setattr(module, "get_auth_client", lambda _config: sync_ok)

    module.session.clear()
    module.session["oauth_state"] = "expected"
    _set_request_args(monkeypatch, module, {"state": "wrong", "code": "code"})
    res = _run(module.oauth_callback("github"))
    assert res["redirect"] == "/?error=invalid_state"

    module.session.clear()
    module.session["oauth_state"] = "ok-state"
    _set_request_args(monkeypatch, module, {"state": "ok-state"})
    res = _run(module.oauth_callback("github"))
    assert res["redirect"] == "/?error=missing_code"

    sync_missing_token = _SyncAuthClient(
        token_info={"id_token": "id-only"},
        user_info=SimpleNamespace(email="sync@example.com", avatar_url="http://img", nickname="sync"),
    )
    monkeypatch.setattr(module, "get_auth_client", lambda _config: sync_missing_token)
    module.session.clear()
    module.session["oauth_state"] = "token-state"
    _set_request_args(monkeypatch, module, {"state": "token-state", "code": "code"})
    res = _run(module.oauth_callback("github"))
    assert res["redirect"] == "/?error=token_failed"

    sync_missing_email = _SyncAuthClient(
        token_info={"access_token": "token-sync", "id_token": "id-sync"},
        user_info=SimpleNamespace(email=None, avatar_url="http://img", nickname="sync"),
    )
    monkeypatch.setattr(module, "get_auth_client", lambda _config: sync_missing_email)
    module.session.clear()
    module.session["oauth_state"] = "email-state"
    _set_request_args(monkeypatch, module, {"state": "email-state", "code": "code"})
    res = _run(module.oauth_callback("github"))
    assert res["redirect"] == "/?error=email_missing"

    async_new_user = _AsyncAuthClient(
        token_info={"access_token": "token-async", "id_token": "id-async"},
        user_info=SimpleNamespace(email="new@example.com", avatar_url="http://img", nickname="new-user"),
    )
    monkeypatch.setattr(module, "get_auth_client", lambda _config: async_new_user)
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [])

    def _raise_download(_url):
        raise RuntimeError("download explode")

    monkeypatch.setattr(module, "download_img", _raise_download)
    monkeypatch.setattr(module, "user_register", lambda _user_id, _user: None)
    rollback_calls = []
    monkeypatch.setattr(module, "rollback_user_registration", lambda user_id: rollback_calls.append(user_id))
    monkeypatch.setattr(module, "get_uuid", lambda: "new-user-id")
    module.session.clear()
    module.session["oauth_state"] = "new-user-state"
    _set_request_args(monkeypatch, module, {"state": "new-user-state", "code": "code"})
    res = _run(module.oauth_callback("github"))
    assert "Failed to register new@example.com" in res["redirect"]
    assert rollback_calls == ["new-user-id"]

    monkeypatch.setattr(module, "download_img", lambda _url: "avatar")
    monkeypatch.setattr(
        module,
        "user_register",
        lambda _user_id, _user: [_DummyUser("dup-1", "new@example.com"), _DummyUser("dup-2", "new@example.com")],
    )
    rollback_calls.clear()
    module.session.clear()
    module.session["oauth_state"] = "dup-user-state"
    _set_request_args(monkeypatch, module, {"state": "dup-user-state", "code": "code"})
    res = _run(module.oauth_callback("github"))
    assert "Same email: new@example.com exists!" in res["redirect"]
    assert rollback_calls == ["new-user-id"]

    new_user = _DummyUser("new-user", "new@example.com")
    login_calls = []
    monkeypatch.setattr(module, "login_user", lambda user: login_calls.append(user))
    monkeypatch.setattr(module, "user_register", lambda _user_id, _user: [new_user])
    module.session.clear()
    module.session["oauth_state"] = "create-user-state"
    _set_request_args(monkeypatch, module, {"state": "create-user-state", "code": "code"})
    res = _run(module.oauth_callback("github"))
    assert res["redirect"] == "/?auth=new-user"
    assert login_calls and login_calls[-1] is new_user

    async_existing_inactive = _AsyncAuthClient(
        token_info={"access_token": "token-existing", "id_token": "id-existing"},
        user_info=SimpleNamespace(email="existing@example.com", avatar_url="http://img", nickname="existing"),
    )
    monkeypatch.setattr(module, "get_auth_client", lambda _config: async_existing_inactive)
    inactive_user = _DummyUser("existing-user", "existing@example.com", is_active="0")
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [inactive_user])
    module.session.clear()
    module.session["oauth_state"] = "inactive-state"
    _set_request_args(monkeypatch, module, {"state": "inactive-state", "code": "code"})
    res = _run(module.oauth_callback("github"))
    assert res["redirect"] == "/?error=user_inactive"

    async_existing_ok = _AsyncAuthClient(
        token_info={"access_token": "token-existing", "id_token": "id-existing"},
        user_info=SimpleNamespace(email="existing@example.com", avatar_url="http://img", nickname="existing"),
    )
    monkeypatch.setattr(module, "get_auth_client", lambda _config: async_existing_ok)
    existing_user = _DummyUser("existing-user", "existing@example.com")
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [existing_user])
    login_calls.clear()
    monkeypatch.setattr(module, "login_user", lambda user: login_calls.append(user))
    monkeypatch.setattr(module, "get_uuid", lambda: "existing-token")
    module.session.clear()
    module.session["oauth_state"] = "existing-state"
    _set_request_args(monkeypatch, module, {"state": "existing-state", "code": "code"})
    res = _run(module.oauth_callback("github"))
    assert res["redirect"] == "/?auth=existing-user"
    assert existing_user.access_token == "existing-token"
    assert existing_user.save_calls == 1
    assert login_calls and login_calls[-1] is existing_user