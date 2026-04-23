async def test_deep_crawl_basic_bfs(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl with limited depth and pages."""
        max_depth = 1
        max_pages = 3 # start_url + 2 more
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS", # Use string value for CacheMode
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                            # Minimal filters for basic test
                            "filter_chain": {
                                "type": "FilterChain",
                                "params": {
                                    "filters": [
                                        {
                                            "type": "DomainFilter",
                                            "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
        response = await async_client.post("/crawl", json=payload)
        response.raise_for_status()
        data = response.json()

        assert data["success"] is True
        assert isinstance(data["results"], list)
        assert len(data["results"]) > 1 # Should be more than just the start URL
        assert len(data["results"]) <= max_pages # Respect max_pages

        found_depth_0 = False
        found_depth_1 = False
        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert DEEP_CRAWL_DOMAIN in result["url"]
            depth = result["metadata"]["depth"]
            assert depth <= max_depth
            if depth == 0: found_depth_0 = True
            if depth == 1: found_depth_1 = True

        assert found_depth_0
        assert found_depth_1