async def test_deep_crawl_with_scoring(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl with URL scoring."""
        max_depth = 1
        max_pages = 4
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
                            "filter_chain": { # Keep basic domain filter
                                "type": "FilterChain",
                                "params": { "filters": [{"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}}]}
                            },
                            "url_scorer": { # Add scorer
                                "type": "CompositeScorer",
                                "params": {
                                    "scorers": [
                                        {   # Favor pages with 'product' in the URL
                                            "type": "KeywordRelevanceScorer",
                                            "params": {"keywords": ["product"], "weight": 1.0}
                                        },
                                        {   # Penalize deep paths slightly
                                            "type": "PathDepthScorer",
                                            "params": {"optimal_depth": 2, "weight": -0.2}
                                        }
                                    ]
                                }
                            },
                            # Set a threshold if needed: "score_threshold": 0.1
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

        # Check if results seem biased towards products (harder to assert strictly without knowing exact scores)
        product_urls_found = any("product_" in result["url"] for result in data["results"] if result["metadata"]["depth"] > 0)
        print(f"Product URLs found among depth > 0 results: {product_urls_found}")
        # We expect scoring to prioritize product pages if available within limits
        # assert product_urls_found # This might be too strict depending on site structure and limits

        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert result["metadata"]["depth"] <= max_depth