async def test_concurrent_raw_requests():
    """Test multiple concurrent raw: requests don't interfere."""
    htmls = [
        f"<html><body><div id='test'>Request {i}</div></body></html>"
        for i in range(5)
    ]

    async with AsyncWebCrawler() as crawler:
        configs = [
            CrawlerRunConfig(
                js_code=f"document.getElementById('test').innerText += ' Modified {i}'"
            )
            for i in range(5)
        ]

        # Run concurrently
        tasks = [
            crawler.arun(f"raw:{html}", config=config)
            for html, config in zip(htmls, configs)
        ]
        results = await asyncio.gather(*tasks)

    for i, result in enumerate(results):
        assert result.success
        assert f"Request {i}" in result.html
        assert f"Modified {i}" in result.html