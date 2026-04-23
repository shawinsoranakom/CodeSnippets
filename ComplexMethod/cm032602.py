def test_webhook_immediate_response_status_and_template_validation(monkeypatch):
    module = _load_agents_app(monkeypatch)
    _patch_background_task(monkeypatch, module)

    def _run_case(response_cfg):
        params = _default_webhook_params(
            security={"auth_type": "none"},
            content_types="application/json",
            response=response_cfg,
        )
        cvs = _make_webhook_cvs(module, params=params)
        monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _id, _cvs=cvs: (True, _cvs))
        monkeypatch.setattr(module, "request", _DummyRequest(headers={"Content-Type": "application/json"}, json_body={}))
        return _run(module.webhook("agent-1"))

    _assert_bad_request(_run_case({"status": "abc"}), "Invalid response status code")
    _assert_bad_request(_run_case({"status": 500}), "must be between 200 and 399")

    empty_res = _run_case({"status": 204, "body_template": ""})
    assert empty_res.status_code == 204
    assert empty_res.content_type == "application/json"
    assert _run(empty_res.get_data(as_text=True)) == "null"

    json_res = _run_case({"status": 201, "body_template": '{"ok": true}'})
    assert json_res.status_code == 201
    assert json_res.content_type == "application/json"
    assert json.loads(_run(json_res.get_data(as_text=True))) == {"ok": True}

    plain_res = _run_case({"status": 202, "body_template": "plain-text"})
    assert plain_res.status_code == 202
    assert plain_res.content_type == "text/plain"
    assert _run(plain_res.get_data(as_text=True)) == "plain-text"