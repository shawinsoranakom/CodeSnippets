def test_logout_setting_profile_matrix_unit(monkeypatch):
    module = _load_user_app(monkeypatch)

    current_user = _DummyUser("current-user", "current@example.com", password="stored-password")
    monkeypatch.setattr(module, "current_user", current_user)
    monkeypatch.setattr(module.secrets, "token_hex", lambda _n: "abcdef")
    logout_calls = []
    monkeypatch.setattr(module, "logout_user", lambda: logout_calls.append(True))

    res = _run(module.log_out())
    assert res["code"] == 0
    assert current_user.access_token == "INVALID_abcdef"
    assert current_user.save_calls == 1
    assert logout_calls == [True]

    _set_request_json(monkeypatch, module, {"password": "old-password", "new_password": "new-password"})
    monkeypatch.setattr(module, "decrypt", lambda value: value)
    monkeypatch.setattr(module, "check_password_hash", lambda _hashed, _plain: False)
    res = _run(module.setting_user())
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR
    assert "Password error" in res["message"]

    _set_request_json(
        monkeypatch,
        module,
        {
            "password": "old-password",
            "new_password": "new-password",
            "nickname": "neo",
            "email": "blocked@example.com",
            "status": "disabled",
            "theme": "dark",
        },
    )
    monkeypatch.setattr(module, "check_password_hash", lambda _hashed, _plain: True)
    monkeypatch.setattr(module, "decrypt", lambda value: f"dec:{value}")
    monkeypatch.setattr(module, "generate_password_hash", lambda value: f"hash:{value}")
    update_calls = {}

    def _update_by_id(user_id, payload):
        update_calls["user_id"] = user_id
        update_calls["payload"] = payload
        return True

    monkeypatch.setattr(module.UserService, "update_by_id", _update_by_id)
    res = _run(module.setting_user())
    assert res["code"] == 0
    assert res["data"] is True
    assert update_calls["user_id"] == "current-user"
    assert update_calls["payload"]["password"] == "hash:dec:new-password"
    assert update_calls["payload"]["nickname"] == "neo"
    assert update_calls["payload"]["theme"] == "dark"
    assert "email" not in update_calls["payload"]
    assert "status" not in update_calls["payload"]

    _set_request_json(monkeypatch, module, {"nickname": "neo"})

    def _raise_update(_user_id, _payload):
        raise RuntimeError("update explode")

    monkeypatch.setattr(module.UserService, "update_by_id", _raise_update)
    res = _run(module.setting_user())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "Update failure" in res["message"]

    res = _run(module.user_profile())
    assert res["code"] == 0
    assert res["data"] == current_user.to_dict()