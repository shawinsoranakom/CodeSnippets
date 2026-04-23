def test_github_callback_matrix_unit(monkeypatch):
    module = _load_user_app(monkeypatch)

    _set_request_args(monkeypatch, module, {"code": "code"})
    module.session.clear()

    async def _request_error(_method, _url, **_kwargs):
        return _DummyHTTPResponse({"error": "bad", "error_description": "boom"})

    monkeypatch.setattr(module, "async_request", _request_error)
    res = _run(module.github_callback())
    assert res["redirect"] == "/?error=boom"

    async def _request_scope_missing(_method, _url, **_kwargs):
        return _DummyHTTPResponse({"scope": "repo", "access_token": "token-gh"})

    monkeypatch.setattr(module, "async_request", _request_scope_missing)
    res = _run(module.github_callback())
    assert res["redirect"] == "/?error=user:email not in scope"

    async def _request_token(_method, _url, **_kwargs):
        return _DummyHTTPResponse({"scope": "user:email,repo", "access_token": "token-gh"})

    monkeypatch.setattr(module, "async_request", _request_token)
    monkeypatch.setattr(
        module,
        "user_info_from_github",
        lambda _token: _AwaitableValue({"email": "gh@example.com", "avatar_url": "http://img", "login": "gh-user"}),
    )
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [])
    rollback_calls = []
    monkeypatch.setattr(module, "rollback_user_registration", lambda user_id: rollback_calls.append(user_id))
    monkeypatch.setattr(module, "get_uuid", lambda: "gh-user-id")

    def _raise_download(_url):
        raise RuntimeError("download explode")

    monkeypatch.setattr(module, "download_img", _raise_download)
    monkeypatch.setattr(module, "user_register", lambda _user_id, _user: None)
    res = _run(module.github_callback())
    assert "Fail to register gh@example.com." in res["redirect"]
    assert rollback_calls == ["gh-user-id"]

    monkeypatch.setattr(module, "download_img", lambda _url: "avatar")
    monkeypatch.setattr(
        module,
        "user_register",
        lambda _user_id, _user: [_DummyUser("dup-1", "gh@example.com"), _DummyUser("dup-2", "gh@example.com")],
    )
    rollback_calls.clear()
    res = _run(module.github_callback())
    assert "Same email: gh@example.com exists!" in res["redirect"]
    assert rollback_calls == ["gh-user-id"]

    new_user = _DummyUser("gh-new-user", "gh@example.com")
    login_calls = []
    monkeypatch.setattr(module, "login_user", lambda user: login_calls.append(user))
    monkeypatch.setattr(module, "user_register", lambda _user_id, _user: [new_user])
    res = _run(module.github_callback())
    assert res["redirect"] == "/?auth=gh-new-user"
    assert login_calls and login_calls[-1] is new_user

    inactive_user = _DummyUser("gh-existing", "gh@example.com", is_active="0")
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [inactive_user])
    res = _run(module.github_callback())
    assert res["redirect"] == "/?error=user_inactive"

    existing_user = _DummyUser("gh-existing", "gh@example.com")
    login_calls.clear()
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [existing_user])
    monkeypatch.setattr(module, "login_user", lambda user: login_calls.append(user))
    monkeypatch.setattr(module, "get_uuid", lambda: "gh-existing-token")
    res = _run(module.github_callback())
    assert res["redirect"] == "/?auth=gh-existing"
    assert existing_user.access_token == "gh-existing-token"
    assert existing_user.save_calls == 1
    assert login_calls and login_calls[-1] is existing_user