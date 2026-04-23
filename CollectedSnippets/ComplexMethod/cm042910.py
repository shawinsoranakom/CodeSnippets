async def test_dfs_basic(local_server):
    """DFS deep crawl at depth 2 should find both sub pages and leaf pages."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    strategy = DFSDeepCrawlStrategy(max_depth=2, max_pages=10)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        urls = [r.url for r in result_list]

        sub_pages = [u for u in urls if "/deep/sub" in u and "leaf" not in u]
        leaf_pages = [u for u in urls if "leaf" in u]

        assert len(sub_pages) >= 1, "DFS should visit at least one sub page"
        assert len(leaf_pages) >= 1, "DFS at depth 2 should visit at least one leaf page"