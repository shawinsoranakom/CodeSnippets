def test_init_oauth_html_chars_are_escaped():
    xss_payload = "Evil</script><script>alert(1)</script>"
    html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Test",
        init_oauth={"appName": xss_payload},
    )
    body = html.body.decode()

    assert "</script><script>" not in body
    assert "\\u003c/script\\u003e\\u003cscript\\u003e" in body