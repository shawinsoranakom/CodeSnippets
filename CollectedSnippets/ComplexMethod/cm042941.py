async def test_multi_url_crawl(self, async_client: httpx.AsyncClient):
        """Test /crawl with multiple URLs, implicitly testing dispatcher."""
        urls = [SIMPLE_HTML_URL, "https://httpbin.org/links/10/0"]
        payload = {
            "urls": urls,
            "browser_config": {
                "type": "BrowserConfig",
                "params": {"headless": True}
            },
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {"stream": False, "cache_mode": CacheMode.BYPASS.value}
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
        assert len(data["results"]) == len(urls)
        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert result["url"] in urls