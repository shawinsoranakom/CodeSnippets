async def test_extract_website_content_handles_http_error(monkeypatch):
    block = ExtractWebsiteContentBlock()
    input_data = block.Input(
        url="https://example.com",
        credentials=cast(JinaCredentialsInput, TEST_CREDENTIALS_INPUT),
        raw_content=False,
    )

    async def fake_get_request(url, json=False, headers=None):
        raise HTTPClientError("HTTP 400 Error: Bad Request", 400)

    monkeypatch.setattr(block, "get_request", fake_get_request)

    results = [
        output
        async for output in block.run(
            input_data=input_data, credentials=TEST_CREDENTIALS
        )
    ]

    assert ("content", "page content") not in results
    error_messages = [value for key, value in results if key == "error"]
    assert error_messages
    assert "Client error (400)" in error_messages[0]
    assert "https://example.com" in error_messages[0]