def test_feishu_callback_matrix_unit(monkeypatch):
    module = _load_user_app(monkeypatch)

    _set_request_args(monkeypatch, module, {"code": "code"})
    module.session.clear()

    def _patch_async_queue(payloads):
        queue = list(payloads)

        async def _request(_method, _url, **_kwargs):
            return _DummyHTTPResponse(queue.pop(0))

        monkeypatch.setattr(module, "async_request", _request)

    _patch_async_queue([{"code": 1}])
    res = _run(module.feishu_callback())
    assert "/?error=" in res["redirect"]

    _patch_async_queue(
        [
            {"code": 0, "app_access_token": "app-token"},
            {"code": 1, "message": "bad token"},
        ]
    )
    res = _run(module.feishu_callback())
    assert res["redirect"] == "/?error=bad token"

    _patch_async_queue(
        [
            {"code": 0, "app_access_token": "app-token"},
            {"code": 0, "data": {"scope": "other", "access_token": "feishu-access"}},
        ]
    )
    res = _run(module.feishu_callback())
    assert "contact:user.email:readonly not in scope" in res["redirect"]

    _patch_async_queue(
        [
            {"code": 0, "app_access_token": "app-token"},
            {"code": 0, "data": {"scope": "contact:user.email:readonly", "access_token": "feishu-access"}},
        ]
    )
    monkeypatch.setattr(
        module,
        "user_info_from_feishu",
        lambda _token: _AwaitableValue({"email": "fs@example.com", "avatar_url": "http://img", "en_name": "fs-user"}),
    )
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [])
    rollback_calls = []
    monkeypatch.setattr(module, "rollback_user_registration", lambda user_id: rollback_calls.append(user_id))
    monkeypatch.setattr(module, "get_uuid", lambda: "fs-user-id")

    def _raise_download(_url):
        raise RuntimeError("download explode")

    monkeypatch.setattr(module, "download_img", _raise_download)
    monkeypatch.setattr(module, "user_register", lambda _user_id, _user: None)
    res = _run(module.feishu_callback())
    assert "Fail to register fs@example.com." in res["redirect"]
    assert rollback_calls == ["fs-user-id"]

    _patch_async_queue(
        [
            {"code": 0, "app_access_token": "app-token"},
            {"code": 0, "data": {"scope": "contact:user.email:readonly", "access_token": "feishu-access"}},
        ]
    )
    monkeypatch.setattr(module, "download_img", lambda _url: "avatar")
    monkeypatch.setattr(
        module,
        "user_register",
        lambda _user_id, _user: [_DummyUser("dup-1", "fs@example.com"), _DummyUser("dup-2", "fs@example.com")],
    )
    rollback_calls.clear()
    res = _run(module.feishu_callback())
    assert "Same email: fs@example.com exists!" in res["redirect"]
    assert rollback_calls == ["fs-user-id"]

    _patch_async_queue(
        [
            {"code": 0, "app_access_token": "app-token"},
            {"code": 0, "data": {"scope": "contact:user.email:readonly", "access_token": "feishu-access"}},
        ]
    )
    new_user = _DummyUser("fs-new-user", "fs@example.com")
    login_calls = []
    monkeypatch.setattr(module, "login_user", lambda user: login_calls.append(user))
    monkeypatch.setattr(module, "user_register", lambda _user_id, _user: [new_user])
    res = _run(module.feishu_callback())
    assert res["redirect"] == "/?auth=fs-new-user"
    assert login_calls and login_calls[-1] is new_user

    _patch_async_queue(
        [
            {"code": 0, "app_access_token": "app-token"},
            {"code": 0, "data": {"scope": "contact:user.email:readonly", "access_token": "feishu-access"}},
        ]
    )
    inactive_user = _DummyUser("fs-existing", "fs@example.com", is_active="0")
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [inactive_user])
    res = _run(module.feishu_callback())
    assert res["redirect"] == "/?error=user_inactive"

    _patch_async_queue(
        [
            {"code": 0, "app_access_token": "app-token"},
            {"code": 0, "data": {"scope": "contact:user.email:readonly", "access_token": "feishu-access"}},
        ]
    )
    existing_user = _DummyUser("fs-existing", "fs@example.com")
    login_calls.clear()
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [existing_user])
    monkeypatch.setattr(module, "login_user", lambda user: login_calls.append(user))
    monkeypatch.setattr(module, "get_uuid", lambda: "fs-existing-token")
    res = _run(module.feishu_callback())
    assert res["redirect"] == "/?auth=fs-existing"
    assert existing_user.access_token == "fs-existing-token"
    assert existing_user.save_calls == 1
    assert login_calls and login_calls[-1] is existing_user