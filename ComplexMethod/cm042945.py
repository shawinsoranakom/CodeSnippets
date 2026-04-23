async def test_json_css_extraction(self, async_client: httpx.AsyncClient):
        """Test /crawl with JsonCssExtractionStrategy."""
        payload = {
            "urls": [SCRAPE_TARGET_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "cache_mode": CacheMode.BYPASS.value,
                    "extraction_strategy": {
                        "type": "JsonCssExtractionStrategy",
                        "params": {
                            "schema": { 
                                "type": "dict", # IMPORTANT: Wrap schema dict with type/value structure
                                "value": {
                                    "name": "BookList",
                                    "baseSelector": "ol.row li.col-xs-6", # Select each book item
                                    "fields": [
                                        {"name": "title", "selector": "article.product_pod h3 a", "type": "attribute", "attribute": "title"},
                                        {"name": "price", "selector": "article.product_pod .price_color", "type": "text"},
                                        {"name": "rating", "selector": "article.product_pod p.star-rating", "type": "attribute", "attribute": "class"}
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
        assert len(data["results"]) == 1
        result = data["results"][0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert "extracted_content" in result
        assert result["extracted_content"] is not None

        # Extracted content should be a JSON string representing a list of dicts
        try:
            extracted_data = json.loads(result["extracted_content"])
            assert isinstance(extracted_data, list)
            assert len(extracted_data) > 0 # Should find some books
            # Check structure of the first extracted item
            first_item = extracted_data[0]
            assert "title" in first_item
            assert "price" in first_item
            assert "rating" in first_item
            assert "star-rating" in first_item["rating"] # e.g., "star-rating Three"
        except (json.JSONDecodeError, AssertionError) as e:
            pytest.fail(f"Extracted content parsing or validation failed: {e}\nContent: {result['extracted_content']}")