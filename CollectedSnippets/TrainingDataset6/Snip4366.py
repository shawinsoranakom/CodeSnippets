def test_normal_init_oauth_still_works():
    html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Test",
        init_oauth={"clientId": "my-client", "appName": "My App"},
    )
    body = html.body.decode()
    assert '"clientId": "my-client"' in body
    assert '"appName": "My App"' in body
    assert "ui.initOAuth" in body