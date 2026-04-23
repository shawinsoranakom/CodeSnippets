async def test_scrape_web_page(browser_type, use_proxy, kwagrs, proxy, capfd, http_server):
    server, url = await http_server()
    urls = [url, url, url]
    proxy_url = None
    if use_proxy:
        proxy_server, proxy_url = await proxy()
    browser = web_browser_engine_playwright.PlaywrightWrapper(browser_type=browser_type, proxy=proxy_url, **kwagrs)
    result = await browser.run(url)
    assert isinstance(result, WebPage)
    assert "MetaGPT" in result.inner_text

    if urls:
        results = await browser.run(url, *urls)
        assert isinstance(results, list)
        assert len(results) == len(urls) + 1
        assert all(("MetaGPT" in i.inner_text) for i in results)
    if use_proxy:
        proxy_server.close()
        await proxy_server.wait_closed()
        assert "Proxy:" in capfd.readouterr().out
    await server.stop()