async def test_deep_crawl_with_ssl(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl with fetch_ssl_certificate enabled."""
        max_depth = 0 # Only fetch for start URL to keep test fast
        max_pages = 1
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "fetch_ssl_certificate": True, # <-- Enable SSL fetching
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                        }
                    }
                }
            }
        }
        response = await async_client.post("/crawl", json=payload)
        response.raise_for_status()
        data = response.json()

        assert data["success"] is True
        assert len(data["results"]) == 1
        result = data["results"][0]

        await assert_crawl_result_structure(result, check_ssl=True) # <-- Tell helper to check SSL field
        assert result["success"] is True
                # Check if SSL info was actually retrieved
        if result["ssl_certificate"]:
            # Assert directly using dictionary keys
            assert isinstance(result["ssl_certificate"], dict) # Verify it's a dict
            assert "issuer" in result["ssl_certificate"]
            assert "subject" in result["ssl_certificate"]
            # --- MODIFIED ASSERTIONS ---
            assert "not_before" in result["ssl_certificate"] # Check for the actual key
            assert "not_after" in result["ssl_certificate"]  # Check for the actual key
            # --- END MODIFICATIONS ---
            assert "fingerprint" in result["ssl_certificate"] # Check another key

            # This print statement using .get() already works correctly with dictionaries
            print(f"SSL Issuer Org: {result['ssl_certificate'].get('issuer', {}).get('O', 'N/A')}")
            print(f"SSL Valid From: {result['ssl_certificate'].get('not_before', 'N/A')}")
        else:
            # This part remains the same
            print("SSL Certificate was null in the result.")