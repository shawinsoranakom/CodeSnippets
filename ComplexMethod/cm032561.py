def test_login_route_branch_matrix_unit(monkeypatch):
    module = _load_user_app(monkeypatch)

    _set_request_json(monkeypatch, module, {})
    res = _run(module.login())
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR
    assert "Unauthorized" in res["message"]

    _set_request_json(monkeypatch, module, {"email": "unknown@example.com", "password": "enc"})
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [])
    res = _run(module.login())
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR
    assert "not registered" in res["message"]

    _set_request_json(monkeypatch, module, {"email": "known@example.com", "password": "enc"})
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [SimpleNamespace(email="known@example.com")])

    def _raise_decrypt(_value):
        raise RuntimeError("decrypt explode")

    monkeypatch.setattr(module, "decrypt", _raise_decrypt)
    res = _run(module.login())
    assert res["code"] == module.RetCode.SERVER_ERROR
    assert "Fail to crypt password" in res["message"]

    user_inactive = _DummyUser("u-inactive", "known@example.com", is_active="0")
    monkeypatch.setattr(module, "decrypt", lambda value: value)
    monkeypatch.setattr(module.UserService, "query_user", lambda _email, _password: user_inactive)
    res = _run(module.login())
    assert res["code"] == module.RetCode.FORBIDDEN
    assert "disabled" in res["message"]

    monkeypatch.setattr(module.UserService, "query_user", lambda _email, _password: None)
    res = _run(module.login())
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR
    assert "do not match" in res["message"]