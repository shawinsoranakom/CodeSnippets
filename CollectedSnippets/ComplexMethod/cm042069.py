async def test_browser_report(http_server):
    img = b"\x89PNG\r\n\x1a\n\x00\x00"
    web_url = "https://docs.deepwisdom.ai"

    class AsyncPage:
        async def screenshot(self):
            return img

    async with callback_server(http_server) as (url, callback_data):
        async with BrowserReporter(callback_url=url) as reporter:
            await reporter.async_report(web_url, "url")
            await reporter.async_report(AsyncPage(), "page")

    assert all(BlockType.BROWSER is BlockType(i["block"]) for i in callback_data)
    assert all(i["uuid"] == callback_data[0]["uuid"] for i in callback_data[1:])
    assert len(callback_data) == 3
    assert callback_data[-1]["name"] == END_MARKER_NAME
    assert callback_data[0]["name"] == "url"
    assert callback_data[0]["value"] == web_url
    assert callback_data[1]["name"] == "page"
    assert ast.literal_eval(callback_data[1]["value"]) == img