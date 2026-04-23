async def test_dfs_depth_first_order(local_server):
    """DFS should explore depth-first: some leaf page should appear before all sub pages are visited."""
    base = _to_ip_url(local_server)
    hub_url = base + "/deep/hub"
    # Give enough pages to see the DFS pattern
    strategy = DFSDeepCrawlStrategy(max_depth=2, max_pages=15)
    config = CrawlerRunConfig(deep_crawl_strategy=strategy, verbose=False)

    async with AsyncWebCrawler(config=BrowserConfig(headless=True, verbose=False)) as crawler:
        results = await crawler.arun(url=hub_url, config=config)

        result_list = list(results)
        urls = [r.url for r in result_list]

        # Find indices of sub pages and leaf pages
        sub_indices = [i for i, u in enumerate(urls) if "/deep/sub" in u and "leaf" not in u]
        leaf_indices = [i for i, u in enumerate(urls) if "leaf" in u]

        if sub_indices and leaf_indices:
            # In DFS, at least one leaf should appear before the last sub page
            earliest_leaf = min(leaf_indices)
            latest_sub = max(sub_indices)
            assert earliest_leaf < latest_sub, (
                "DFS should explore a branch deeply before exhausting all sub pages. "
                f"Earliest leaf at index {earliest_leaf}, latest sub at index {latest_sub}."
            )