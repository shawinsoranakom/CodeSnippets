def test_connector_oauth_helper_functions(monkeypatch):
    module = _load_connector_app(monkeypatch)

    assert module._web_state_cache_key("flow-a", "gmail") == "gmail_web_flow_state:flow-a"
    assert module._web_result_cache_key("flow-b", "google-drive") == "google-drive_web_flow_result:flow-b"

    creds_dict = {"web": {"client_id": "id"}}
    assert module._load_credentials(creds_dict) == creds_dict
    assert module._load_credentials(json.dumps(creds_dict)) == creds_dict

    with pytest.raises(ValueError, match="Invalid Google credentials JSON"):
        module._load_credentials("{not-json")

    assert module._get_web_client_config(creds_dict) == {"web": {"client_id": "id"}}
    with pytest.raises(ValueError, match="must include a 'web'"):
        module._get_web_client_config({"installed": {"client_id": "id"}})

    popup_ok = _run(module._render_web_oauth_popup("flow-1", True, "done", "gmail"))
    assert popup_ok.status_code == 200
    assert popup_ok.headers["Content-Type"] == "text/html; charset=utf-8"
    assert "Authorization complete" in popup_ok.body
    assert "ragflow-gmail-oauth" in popup_ok.body

    popup_error = _run(module._render_web_oauth_popup("flow-2", False, "<denied>", "google-drive"))
    assert popup_error.status_code == 200
    assert "Authorization failed" in popup_error.body
    assert "&lt;denied&gt;" in popup_error.body