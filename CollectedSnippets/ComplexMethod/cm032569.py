def test_forget_reset_password_matrix_unit(monkeypatch):
    module = _load_user_app(monkeypatch)
    email = "reset@example.com"
    v_key = module._verified_key(email)
    user = _DummyUser("u-reset", email, nickname="reset-user")
    pwd_a = base64.b64encode(b"new-password").decode()
    pwd_b = base64.b64encode(b"confirm-password").decode()
    pwd_same = base64.b64encode(b"same-password").decode()
    monkeypatch.setattr(module, "decrypt", lambda value: value)

    _set_request_json(monkeypatch, module, {"email": email, "new_password": pwd_same, "confirm_new_password": pwd_same})
    module.REDIS_CONN.store.pop(v_key, None)
    res = _run(module.forget_reset_password())
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res

    module.REDIS_CONN.store[v_key] = "1"
    monkeypatch.setattr(module, "decrypt", lambda _value: "")
    _set_request_json(monkeypatch, module, {"email": email, "new_password": "", "confirm_new_password": ""})
    res = _run(module.forget_reset_password())
    assert res["code"] == module.RetCode.ARGUMENT_ERROR, res

    monkeypatch.setattr(module, "decrypt", lambda value: value)
    module.REDIS_CONN.store[v_key] = "1"
    _set_request_json(monkeypatch, module, {"email": email, "new_password": pwd_a, "confirm_new_password": pwd_b})
    res = _run(module.forget_reset_password())
    assert res["code"] == module.RetCode.ARGUMENT_ERROR, res
    assert "do not match" in res["message"], res

    module.REDIS_CONN.store[v_key] = "1"
    monkeypatch.setattr(module.UserService, "query_user_by_email", lambda **_kwargs: [])
    _set_request_json(monkeypatch, module, {"email": email, "new_password": pwd_same, "confirm_new_password": pwd_same})
    res = _run(module.forget_reset_password())
    assert res["code"] == module.RetCode.DATA_ERROR, res

    module.REDIS_CONN.store[v_key] = "1"
    monkeypatch.setattr(module.UserService, "query_user_by_email", lambda **_kwargs: [user])

    def _raise_update_password(_user_id, _new_pwd):
        raise RuntimeError("reset boom")

    monkeypatch.setattr(module.UserService, "update_user_password", _raise_update_password)
    _set_request_json(monkeypatch, module, {"email": email, "new_password": pwd_same, "confirm_new_password": pwd_same})
    res = _run(module.forget_reset_password())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res

    module.REDIS_CONN.store[v_key] = "1"
    monkeypatch.setattr(module.UserService, "update_user_password", lambda _user_id, _new_pwd: True)
    monkeypatch.setattr(module.REDIS_CONN, "delete", lambda _key: (_ for _ in ()).throw(RuntimeError("delete boom")))
    _set_request_json(monkeypatch, module, {"email": email, "new_password": pwd_same, "confirm_new_password": pwd_same})
    res = _run(module.forget_reset_password())
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["auth"] == user.get_id(), res

    monkeypatch.setattr(module.REDIS_CONN, "delete", lambda key: module.REDIS_CONN.store.pop(key, None))
    module.REDIS_CONN.store[v_key] = "1"
    _set_request_json(monkeypatch, module, {"email": email, "new_password": pwd_same, "confirm_new_password": pwd_same})
    res = _run(module.forget_reset_password())
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["auth"] == user.get_id(), res
    assert module.REDIS_CONN.get(v_key) is None, module.REDIS_CONN.store