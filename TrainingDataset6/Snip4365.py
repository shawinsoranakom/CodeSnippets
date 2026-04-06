def test_swagger_ui_parameters_html_chars_are_escaped():
    html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Test",
        swagger_ui_parameters={"customKey": "<img src=x onerror=alert(1)>"},
    )
    body = html.body.decode()
    assert "<img src=x onerror=alert(1)>" not in body
    assert "\\u003cimg" in body