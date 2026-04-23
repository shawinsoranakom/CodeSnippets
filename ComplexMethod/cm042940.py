async def test_crawl_with_stream_direct(self, async_client: httpx.AsyncClient):
        """Test that /crawl endpoint handles stream=True directly without redirect."""
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
                    "stream": True,  # Set stream to True for direct streaming
                    "screenshot": False,
                    "cache_mode": CacheMode.BYPASS.value
                }
            }
        }

        # Send a request to the /crawl endpoint - should handle streaming directly
        async with async_client.stream("POST", "/crawl", json=payload) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/x-ndjson"
            assert response.headers.get("x-stream-status") == "active"

            results = await process_streaming_response(response)

            assert len(results) == 1
            result = results[0]
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert result["url"] == SIMPLE_HTML_URL
            assert "<h1>Herman Melville - Moby-Dick</h1>" in result["html"]