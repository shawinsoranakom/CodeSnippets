def test_webhook_token_basic_jwt_auth(monkeypatch):
    module = _load_agents_app(monkeypatch)
    _patch_background_task(monkeypatch, module)

    monkeypatch.setattr(module, "request", _DummyRequest(headers={"Content-Type": "application/json"}, json_body={}))

    token_security = {"auth_type": "token", "token": {"token_header": "X-TOKEN", "token_value": "ok"}}
    cvs = _make_webhook_cvs(module, params=_default_webhook_params(security=token_security))
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id: (True, cvs))
    _assert_bad_request(_run(module.webhook("agent-1")), "Invalid token authentication")

    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(
            headers={"Content-Type": "application/json"},
            json_body={},
            authorization=SimpleNamespace(username="u", password="bad"),
        ),
    )
    basic_security = {"auth_type": "basic", "basic_auth": {"username": "u", "password": "p"}}
    cvs = _make_webhook_cvs(module, params=_default_webhook_params(security=basic_security))
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id: (True, cvs))
    _assert_bad_request(_run(module.webhook("agent-1")), "Invalid Basic Auth credentials")

    monkeypatch.setattr(module, "request", _DummyRequest(headers={"Content-Type": "application/json"}, json_body={}))
    jwt_missing_secret = {"auth_type": "jwt", "jwt": {}}
    cvs = _make_webhook_cvs(module, params=_default_webhook_params(security=jwt_missing_secret))
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id: (True, cvs))
    _assert_bad_request(_run(module.webhook("agent-1")), "JWT secret not configured")

    jwt_base = {"auth_type": "jwt", "jwt": {"secret": "secret"}}
    cvs = _make_webhook_cvs(module, params=_default_webhook_params(security=jwt_base))
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id: (True, cvs))
    _assert_bad_request(_run(module.webhook("agent-1")), "Missing Bearer token")

    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(headers={"Content-Type": "application/json", "Authorization": "Bearer   "}, json_body={}),
    )
    _assert_bad_request(_run(module.webhook("agent-1")), "Empty Bearer token")

    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(headers={"Content-Type": "application/json", "Authorization": "Bearer token"}, json_body={}),
    )
    monkeypatch.setattr(module.jwt, "decode", lambda *_args, **_kwargs: (_ for _ in ()).throw(Exception("decode boom")))
    _assert_bad_request(_run(module.webhook("agent-1")), "Invalid JWT")

    monkeypatch.setattr(module.jwt, "decode", lambda *_args, **_kwargs: {"exp": 1})
    jwt_reserved = {"auth_type": "jwt", "jwt": {"secret": "secret", "required_claims": ["exp"]}}
    cvs = _make_webhook_cvs(module, params=_default_webhook_params(security=jwt_reserved))
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id: (True, cvs))
    _assert_bad_request(_run(module.webhook("agent-1")), "Reserved JWT claim cannot be required")

    monkeypatch.setattr(module.jwt, "decode", lambda *_args, **_kwargs: {})
    jwt_missing_claim = {"auth_type": "jwt", "jwt": {"secret": "secret", "required_claims": ["role"]}}
    cvs = _make_webhook_cvs(module, params=_default_webhook_params(security=jwt_missing_claim))
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id: (True, cvs))
    _assert_bad_request(_run(module.webhook("agent-1")), "Missing JWT claim")

    captured = {}

    def fake_decode(token, options, **kwargs):
        captured["token"] = token
        captured["options"] = options
        captured["kwargs"] = kwargs
        return {"role": "admin"}

    monkeypatch.setattr(module.jwt, "decode", fake_decode)
    jwt_success = {
        "auth_type": "jwt",
        "jwt": {
            "secret": "secret",
            "audience": "aud",
            "issuer": "iss",
            "required_claims": "role",
        },
    }
    cvs = _make_webhook_cvs(module, params=_default_webhook_params(security=jwt_success))
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id: (True, cvs))
    res = _run(module.webhook("agent-1"))
    assert hasattr(res, "status_code")
    assert res.status_code == 200
    assert captured["kwargs"]["audience"] == "aud"
    assert captured["kwargs"]["issuer"] == "iss"
    assert captured["options"]["verify_aud"] is True
    assert captured["options"]["verify_iss"] is True

    monkeypatch.setattr(module.jwt, "decode", lambda *_args, **_kwargs: {})
    jwt_success_invalid_type = {"auth_type": "jwt", "jwt": {"secret": "secret", "required_claims": 123}}
    cvs = _make_webhook_cvs(module, params=_default_webhook_params(security=jwt_success_invalid_type))
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id: (True, cvs))
    res = _run(module.webhook("agent-1"))
    assert hasattr(res, "status_code")
    assert res.status_code == 200