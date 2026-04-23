async def test_mixed_success_failure_urls(self, async_client: httpx.AsyncClient):
        """Test handling of mixed success/failure URLs."""
        payload = {
            "urls": [
                SIMPLE_HTML_URL,  # Should succeed
                "https://nonexistent-domain-12345.com",  # Should fail
                "https://invalid-url-with-special-chars-!@#$%^&*()",  # Should fail
            ],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig", 
                "params": {
                    "cache_mode": CacheMode.BYPASS.value,
                    "markdown_generator": {
                        "type": "DefaultMarkdownGenerator",
                        "params": {
                            "content_filter": {
                                "type": "PruningContentFilter",
                                "params": {"threshold": 0.5}
                            }
                        }
                    }
                }
            }
        }

        response = await async_client.post("/crawl", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["results"]) == 3

        success_count = 0
        failure_count = 0

        for result in data["results"]:
            if result["success"]:
                success_count += 1
            else:
                failure_count += 1
                assert "error_message" in result
                assert len(result["error_message"]) > 0

        assert success_count >= 1  # At least one should succeed
        assert failure_count >= 1