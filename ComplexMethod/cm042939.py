async def test_simple_crawl_single_url(self, async_client: httpx.AsyncClient):
        """Test /crawl with a single URL and simple config values."""
        payload = {
            "urls": [SIMPLE_HTML_URL],
            "browser_config": {
                "type": "BrowserConfig",
                "params": {
                    "headless": True,
                }
            },
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False, # Explicitly false for /crawl
                    "screenshot": False,
                    "cache_mode": CacheMode.BYPASS.value # Use enum value
                }
            }
        }
        try:
            response = await async_client.post("/crawl", json=payload)
            print(f"Response status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as e:
            print(f"Server error: {e}")
            print(f"Response content: {e.response.text}")
            raise

        assert data["success"] is True
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 1
        result = data["results"][0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert result["url"] == SIMPLE_HTML_URL
        assert "<h1>Herman Melville - Moby-Dick</h1>" in result["html"]