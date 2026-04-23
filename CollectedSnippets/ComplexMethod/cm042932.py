async def test_deep_crawl_with_filters(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl with content type and domain filters."""
        max_depth = 1
        max_pages = 5
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                            "filter_chain": {
                                "type": "FilterChain",
                                "params": {
                                    "filters": [
                                        {
                                            "type": "DomainFilter",
                                            "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}
                                        },
                                        {
                                            "type": "ContentTypeFilter",
                                            "params": {"allowed_types": ["text/html"]}
                                        },
                                        # Example: Exclude specific paths using regex
                                        {
                                            "type": "URLPatternFilter",
                                             "params": {
                                                 "patterns": ["*/category-3/*"], # Block category 3
                                                 "reverse": True # Block if match
                                             }
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
        assert len(data["results"]) > 0
        assert len(data["results"]) <= max_pages

        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert DEEP_CRAWL_DOMAIN in result["url"]
            assert "category-3" not in result["url"] # Check if filter worked
            assert result["metadata"]["depth"] <= max_depth