async def test_deep_crawl(self, async_client: httpx.AsyncClient):
        """Test /crawl with a deep crawl strategy."""
        payload = {
            "urls": [DEEP_CRAWL_URL], # Start URL
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": CacheMode.BYPASS.value,
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": 1, # Limit depth for testing speed
                            "max_pages": 5, # Limit pages to crawl
                            "filter_chain": {
                                "type": "FilterChain",
                                "params": {
                                    "filters": [
                                        {
                                            "type": "ContentTypeFilter",
                                            "params": {"allowed_types": ["text/html"]}
                                        },
                                        {
                                            "type": "DomainFilter",
                                            "params": {"allowed_domains": ["python.org", "docs.python.org"]} # Include important subdomains
                                        }
                                    ]
                                }
                            },
                            "url_scorer": {
                                "type": "CompositeScorer",
                                "params": {
                                    "scorers": [
                                        {
                                            "type": "KeywordRelevanceScorer",
                                            "params": {"keywords": ["documentation", "tutorial"]}
                                        },
                                        {
                                            "type": "PathDepthScorer",
                                            "params": {"weight": 0.5, "optimal_depth": 2}
                                        }
                                    ]
                                }
                            }
                        }
                    }
                }
            }
        }
        try:
            print(f"Sending deep crawl request to server...")
            response = await async_client.post("/crawl", json=payload)
            print(f"Response status: {response.status_code}")

            if response.status_code >= 400:
                error_detail = response.json().get('detail', 'No detail provided')
                print(f"Error detail: {error_detail}")
                print(f"Full response: {response.text}")

            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"Server error status: {e.response.status_code}")
            print(f"Server error response: {e.response.text}")
            try:
                error_json = e.response.json()
                print(f"Parsed error: {error_json}")
            except:
                print("Could not parse error response as JSON")
            raise

        assert data["success"] is True
        assert isinstance(data["results"], list)
        # Expect more than 1 result due to deep crawl (start URL + crawled links)
        assert len(data["results"]) > 1
        assert len(data["results"]) <= 6 # Start URL + max_links=5

        start_url_found = False
        crawled_urls_found = False
        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True

            # Print URL for debugging
            print(f"Crawled URL: {result['url']}")

            # Allow URLs that contain python.org (including subdomains like docs.python.org)
            assert "python.org" in result["url"]
            if result["url"] == DEEP_CRAWL_URL:
                start_url_found = True
            else:
                crawled_urls_found = True

        assert start_url_found
        assert crawled_urls_found