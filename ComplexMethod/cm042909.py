async def test_bfs_basic(local_server):
    """BFS deep crawl of /deep/hub at depth 1 should return hub + sub pages."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = BFSDeepCrawlStrategy(max_depth=1, max_pages=10)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        assert len(result_list) >= 1, "Should return at least the hub page"

        # First result should be the hub
        assert "/deep/hub" in result_list[0].url, "First result should be the hub page"

        # Check sub pages are present
        sub_urls = [r.url for r in result_list if "/deep/sub" in r.url]
        assert len(sub_urls) >= 1, "Should discover at least one sub page"

        # Verify metadata has depth key
        for r in result_list:
            assert r.metadata is not None, "Each result should have metadata"
            assert "depth" in r.metadata, "Metadata should contain 'depth' key"

        # Hub should be at depth 0
        hub_result = result_list[0]
        assert hub_result.metadata["depth"] == 0, "Hub should be at depth 0"

        # Sub pages should be at depth 1
        for r in result_list:
            if "/deep/sub" in r.url:
                assert r.metadata["depth"] == 1, f"Sub page {r.url} should be at depth 1"