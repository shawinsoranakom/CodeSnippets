def test_forget_captcha_and_send_otp_matrix_unit(monkeypatch):
    module = _load_user_app(monkeypatch)

    class _Headers(dict):
        def set(self, key, value):
            self[key] = value

    async def _make_response(data):
        return SimpleNamespace(data=data, headers=_Headers())

    monkeypatch.setattr(module, "make_response", _make_response)

    captcha_pkg = ModuleType("captcha")
    captcha_image_mod = ModuleType("captcha.image")

    class _ImageCaptcha:
        def __init__(self, **_kwargs):
            pass

        def generate(self, text):
            return SimpleNamespace(read=lambda: f"img:{text}".encode())

    captcha_image_mod.ImageCaptcha = _ImageCaptcha
    monkeypatch.setitem(sys.modules, "captcha", captcha_pkg)
    monkeypatch.setitem(sys.modules, "captcha.image", captcha_image_mod)

    _set_request_args(monkeypatch, module, {"email": ""})
    res = _run(module.forget_get_captcha())
    assert res["code"] == module.RetCode.ARGUMENT_ERROR, res

    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [])
    _set_request_args(monkeypatch, module, {"email": "nobody@example.com"})
    res = _run(module.forget_get_captcha())
    assert res["code"] == module.RetCode.DATA_ERROR, res

    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [_DummyUser("u1", "ok@example.com")])
    monkeypatch.setattr(module.secrets, "choice", lambda _allowed: "A")
    _set_request_args(monkeypatch, module, {"email": "ok@example.com"})
    res = _run(module.forget_get_captcha())
    assert res.data.startswith(b"img:"), res
    assert res.headers["Content-Type"] == "image/JPEG", res.headers
    assert module.REDIS_CONN.get(module.captcha_key("ok@example.com")), module.REDIS_CONN.store

    _set_request_json(monkeypatch, module, {"email": "", "captcha": ""})
    res = _run(module.forget_send_otp())
    assert res["code"] == module.RetCode.ARGUMENT_ERROR, res

    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [])
    _set_request_json(monkeypatch, module, {"email": "none@example.com", "captcha": "AAAA"})
    res = _run(module.forget_send_otp())
    assert res["code"] == module.RetCode.DATA_ERROR, res

    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [_DummyUser("u1", "ok@example.com")])
    _set_request_json(monkeypatch, module, {"email": "ok@example.com", "captcha": "AAAA"})
    module.REDIS_CONN.store.pop(module.captcha_key("ok@example.com"), None)
    res = _run(module.forget_send_otp())
    assert res["code"] == module.RetCode.NOT_EFFECTIVE, res

    module.REDIS_CONN.store[module.captcha_key("ok@example.com")] = "ABCD"
    _set_request_json(monkeypatch, module, {"email": "ok@example.com", "captcha": "ZZZZ"})
    res = _run(module.forget_send_otp())
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res

    monkeypatch.setattr(module.time, "time", lambda: 1000)
    k_code, k_attempts, k_last, k_lock = module.otp_keys("ok@example.com")
    module.REDIS_CONN.store[module.captcha_key("ok@example.com")] = "ABCD"
    module.REDIS_CONN.store[k_last] = "990"
    _set_request_json(monkeypatch, module, {"email": "ok@example.com", "captcha": "ABCD"})
    res = _run(module.forget_send_otp())
    assert res["code"] == module.RetCode.NOT_EFFECTIVE, res
    assert "wait" in res["message"], res

    module.REDIS_CONN.store[module.captcha_key("ok@example.com")] = "ABCD"
    module.REDIS_CONN.store[k_last] = "bad-timestamp"
    monkeypatch.setattr(module.secrets, "choice", lambda _allowed: "B")
    monkeypatch.setattr(module.os, "urandom", lambda _n: b"\x00" * 16)
    monkeypatch.setattr(module, "hash_code", lambda code, _salt: f"HASH_{code}")

    async def _raise_send_email(*_args, **_kwargs):
        raise RuntimeError("send email boom")

    monkeypatch.setattr(module, "send_email_html", _raise_send_email)
    _set_request_json(monkeypatch, module, {"email": "ok@example.com", "captcha": "ABCD"})
    res = _run(module.forget_send_otp())
    assert res["code"] == module.RetCode.SERVER_ERROR, res
    assert "failed to send email" in res["message"], res

    async def _ok_send_email(*_args, **_kwargs):
        return True

    module.REDIS_CONN.store[module.captcha_key("ok@example.com")] = "ABCD"
    module.REDIS_CONN.store.pop(k_last, None)
    monkeypatch.setattr(module, "send_email_html", _ok_send_email)
    _set_request_json(monkeypatch, module, {"email": "ok@example.com", "captcha": "ABCD"})
    res = _run(module.forget_send_otp())
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"] is True, res
    assert module.REDIS_CONN.get(k_code), module.REDIS_CONN.store
    assert module.REDIS_CONN.get(k_attempts) == 0, module.REDIS_CONN.store
    assert module.REDIS_CONN.get(k_lock) is None, module.REDIS_CONN.store