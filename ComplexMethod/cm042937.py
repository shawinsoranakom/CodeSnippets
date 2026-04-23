async def test_deep_crawl_with_proxies(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl using proxy rotation."""
        proxies = load_proxies_from_env()
        if not proxies:
            pytest.skip("Skipping proxy test: PROXIES environment variable not set or empty.")

        print(f"\nTesting with {len(proxies)} proxies loaded from environment.")

        max_depth = 1
        max_pages = 3
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL], # Use the dummy site
             # Use a BrowserConfig that *might* pick up proxy if set, but rely on CrawlerRunConfig
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "proxy_rotation_strategy": { # <-- Define the strategy
                        "type": "RoundRobinProxyStrategy",
                        "params": {
                             # Convert ProxyConfig dicts back to the serialized format expected by server
                             "proxies": [{"type": "ProxyConfig", "params": p} for p in proxies]
                        }
                    },
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                            "filter_chain": {
                                "type": "FilterChain",
                                "params": { "filters": [{"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}}]}
                            }
                        }
                    }
                }
            }
        }
        try:
            response = await async_client.post("/crawl", json=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            # Proxies often cause connection errors, catch them
            pytest.fail(f"Proxy deep crawl failed: {e}. Response: {e.response.text}. Are proxies valid and accessible by the server?")
        except httpx.RequestError as e:
             pytest.fail(f"Proxy deep crawl request failed: {e}. Are proxies valid and accessible?")

        assert data["success"] is True
        assert len(data["results"]) > 0
        assert len(data["results"]) <= max_pages
        # Primary assertion is that the crawl succeeded *with* proxy config
        print(f"Proxy deep crawl completed successfully for {len(data['results'])} pages.")