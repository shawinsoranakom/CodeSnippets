async def test_crawl_with_markdown_pruning_filter(self, async_client: httpx.AsyncClient):
        """Test /crawl with MarkdownGenerator using PruningContentFilter."""
        payload = {
            "urls": [SIMPLE_HTML_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "cache_mode": CacheMode.ENABLED.value, # Test different cache mode
                    "markdown_generator": {
                        "type": "DefaultMarkdownGenerator",
                        "params": {
                            "content_filter": {
                                "type": "PruningContentFilter",
                                "params": {
                                    "threshold": 0.5, # Example param
                                    "threshold_type": "relative"
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
        assert len(data["results"]) == 1
        result = data["results"][0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert "markdown" in result
        assert isinstance(result["markdown"], dict)
        assert "raw_markdown" in result["markdown"]
        assert "fit_markdown" in result["markdown"] # Pruning creates fit_markdown
        assert "Moby-Dick" in result["markdown"]["raw_markdown"]
        # Fit markdown content might be different/shorter due to pruning
        assert len(result["markdown"]["fit_markdown"]) <= len(result["markdown"]["raw_markdown"])