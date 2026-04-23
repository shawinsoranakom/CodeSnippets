def test_forget_verify_otp_matrix_unit(monkeypatch):
    module = _load_user_app(monkeypatch)
    email = "ok@example.com"
    k_code, k_attempts, k_last, k_lock = module.otp_keys(email)
    salt = b"\x01" * 16
    monkeypatch.setattr(module, "hash_code", lambda code, _salt: f"HASH_{code}")

    _set_request_json(monkeypatch, module, {})
    res = _run(module.forget_verify_otp())
    assert res["code"] == module.RetCode.ARGUMENT_ERROR, res

    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [])
    _set_request_json(monkeypatch, module, {"email": email, "otp": "ABCDEF"})
    res = _run(module.forget_verify_otp())
    assert res["code"] == module.RetCode.DATA_ERROR, res

    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [_DummyUser("u1", email)])
    module.REDIS_CONN.store[k_lock] = "1"
    _set_request_json(monkeypatch, module, {"email": email, "otp": "ABCDEF"})
    res = _run(module.forget_verify_otp())
    assert res["code"] == module.RetCode.NOT_EFFECTIVE, res
    module.REDIS_CONN.store.pop(k_lock, None)

    module.REDIS_CONN.store.pop(k_code, None)
    _set_request_json(monkeypatch, module, {"email": email, "otp": "ABCDEF"})
    res = _run(module.forget_verify_otp())
    assert res["code"] == module.RetCode.NOT_EFFECTIVE, res

    module.REDIS_CONN.store[k_code] = "broken"
    _set_request_json(monkeypatch, module, {"email": email, "otp": "ABCDEF"})
    res = _run(module.forget_verify_otp())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res

    module.REDIS_CONN.store[k_code] = f"HASH_CORRECT:{salt.hex()}"
    module.REDIS_CONN.store[k_attempts] = "bad-int"
    _set_request_json(monkeypatch, module, {"email": email, "otp": "wrong"})
    res = _run(module.forget_verify_otp())
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res
    assert module.REDIS_CONN.get(k_attempts) == 1, module.REDIS_CONN.store

    module.REDIS_CONN.store[k_code] = f"HASH_CORRECT:{salt.hex()}"
    module.REDIS_CONN.store[k_attempts] = str(module.ATTEMPT_LIMIT - 1)
    _set_request_json(monkeypatch, module, {"email": email, "otp": "wrong"})
    res = _run(module.forget_verify_otp())
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res
    assert module.REDIS_CONN.get(k_lock) is not None, module.REDIS_CONN.store
    module.REDIS_CONN.store.pop(k_lock, None)

    module.REDIS_CONN.store[k_code] = f"HASH_ABCDEF:{salt.hex()}"
    module.REDIS_CONN.store[k_attempts] = "0"
    module.REDIS_CONN.store[k_last] = "1000"

    def _set_with_verified_fail(key, value, _ttl=None):
        if key == module._verified_key(email):
            raise RuntimeError("verified set boom")
        module.REDIS_CONN.store[key] = value

    monkeypatch.setattr(module.REDIS_CONN, "set", _set_with_verified_fail)
    _set_request_json(monkeypatch, module, {"email": email, "otp": "abcdef"})
    res = _run(module.forget_verify_otp())
    assert res["code"] == module.RetCode.SERVER_ERROR, res

    monkeypatch.setattr(module.REDIS_CONN, "set", lambda key, value, _ttl=None: module.REDIS_CONN.store.__setitem__(key, value))
    module.REDIS_CONN.store[k_code] = f"HASH_ABCDEF:{salt.hex()}"
    module.REDIS_CONN.store[k_attempts] = "0"
    module.REDIS_CONN.store[k_last] = "1000"
    _set_request_json(monkeypatch, module, {"email": email, "otp": "abcdef"})
    res = _run(module.forget_verify_otp())
    assert res["code"] == module.RetCode.SUCCESS, res
    assert module.REDIS_CONN.get(k_code) is None, module.REDIS_CONN.store
    assert module.REDIS_CONN.get(k_attempts) is None, module.REDIS_CONN.store
    assert module.REDIS_CONN.get(k_last) is None, module.REDIS_CONN.store
    assert module.REDIS_CONN.get(k_lock) is None, module.REDIS_CONN.store
    assert module.REDIS_CONN.get(module._verified_key(email)) == "1", module.REDIS_CONN.store