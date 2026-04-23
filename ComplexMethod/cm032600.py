def test_webhook_parse_request_branches(monkeypatch):
    module = _load_agents_app(monkeypatch)
    _patch_background_task(monkeypatch, module)

    security = {"auth_type": "none"}
    params = _default_webhook_params(security=security, content_types="application/json")
    cvs = _make_webhook_cvs(module, params=params)
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id: (True, cvs))

    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(headers={"Content-Type": "text/plain"}, raw_body=b'{"x":1}', json_body={}),
    )
    with pytest.raises(ValueError, match="Invalid Content-Type"):
        _run(module.webhook("agent-1"))

    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(headers={"Content-Type": "application/json"}, json_body={"x": 1}, args={"q": "1"}),
    )
    res = _run(module.webhook("agent-1"))
    assert hasattr(res, "status_code")
    assert res.status_code == 200

    params = _default_webhook_params(security=security, content_types="multipart/form-data")
    cvs = _make_webhook_cvs(module, params=params)
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id: (True, cvs))
    files = {f"file{i}": object() for i in range(11)}
    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(
            headers={"Content-Type": "multipart/form-data"},
            form={"key": "value"},
            files=files,
            json_body={},
        ),
    )
    res = _run(module.webhook("agent-1"))
    assert hasattr(res, "status_code")
    assert res.status_code == 200

    uploaded = {"count": 0}
    monkeypatch.setattr(
        module.FileService,
        "upload_info",
        lambda *_args, **_kwargs: uploaded.__setitem__("count", uploaded["count"] + 1) or {"id": "uploaded"},
    )
    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(
            headers={"Content-Type": "multipart/form-data"},
            form={"k": "v"},
            files={"file1": object()},
            json_body={},
        ),
    )
    res = _run(module.webhook("agent-1"))
    assert hasattr(res, "status_code")
    assert res.status_code == 200
    assert uploaded["count"] == 1