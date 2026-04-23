async def test_streaming_mixed_urls(self, async_client: httpx.AsyncClient):
        """Test streaming with mixed success/failure URLs."""
        payload = {
            "urls": [
                SIMPLE_HTML_URL,  # Should succeed
                "https://nonexistent-domain-12345.com",  # Should fail
            ],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig", 
                "params": {
                    "stream": True,
                    "cache_mode": CacheMode.BYPASS.value
                }
            }
        }

        async with async_client.stream("POST", "/crawl/stream", json=payload) as response:
            response.raise_for_status()
            results = await process_streaming_response(response)

        assert len(results) == 2

        success_count = 0
        failure_count = 0

        for result in results:
            if result["success"]:
                success_count += 1
                assert result["url"] == SIMPLE_HTML_URL
            else:
                failure_count += 1
                assert "error_message" in result
                assert result["error_message"] is not None

        assert success_count == 1
        assert failure_count == 1