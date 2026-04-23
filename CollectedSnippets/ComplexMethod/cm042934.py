async def test_deep_crawl_with_css_extraction(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl combined with JsonCssExtractionStrategy."""
        max_depth = 6 # Go deep enough to reach product pages
        max_pages = 20
        # Schema to extract product details
        product_schema = {
            "name": "ProductDetails",
            "baseSelector": "div.container", # Base for product page
            "fields": [
                {"name": "product_title", "selector": "h1", "type": "text"},
                {"name": "price", "selector": ".product-price", "type": "text"},
                {"name": "description", "selector": ".product-description p", "type": "text"},
                {"name": "specs", "selector": ".product-specs li", "type": "list", "fields":[
                     {"name": "spec_name", "selector": ".spec-name", "type": "text"},
                     {"name": "spec_value", "selector": ".spec-value", "type": "text"}
                ]}
            ]
        }
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "extraction_strategy": { # Apply extraction to ALL crawled pages
                        "type": "JsonCssExtractionStrategy",
                        "params": {"schema": {"type": "dict", "value": product_schema}}
                    },
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                            "filter_chain": { # Only crawl HTML on our domain
                                "type": "FilterChain",
                                "params": {
                                    "filters": [
                                        {"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}},
                                        {"type": "ContentTypeFilter", "params": {"allowed_types": ["text/html"]}}
                                    ]
                                }
                            }
                            # Optional: Add scoring to prioritize product pages for extraction
                        }
                    }
                }
            }
        }
        response = await async_client.post("/crawl", json=payload)
        response.raise_for_status()
        data = response.json()

        assert data["success"] is True
        assert len(data["results"]) > 0
        # assert len(data["results"]) <= max_pages

        found_extracted_product = False
        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert "extracted_content" in result
            if "product_" in result["url"]: # Check product pages specifically
                 assert result["extracted_content"] is not None
                 try:
                     extracted = json.loads(result["extracted_content"])
                     # Schema returns list even if one base match
                     assert isinstance(extracted, list)
                     if extracted:
                         item = extracted[0]
                         assert "product_title" in item and item["product_title"]
                         assert "price" in item and item["price"]
                         # Specs might be empty list if not found
                         assert "specs" in item and isinstance(item["specs"], list)
                         found_extracted_product = True
                         print(f"Extracted product: {item.get('product_title')}")
                 except (json.JSONDecodeError, AssertionError, IndexError) as e:
                      pytest.fail(f"Extraction validation failed for {result['url']}: {e}\nContent: {result['extracted_content']}")
            # else:
            #      # Non-product pages might have None or empty list depending on schema match
            #      assert result["extracted_content"] is None or json.loads(result["extracted_content"]) == []

        assert found_extracted_product, "Did not find any pages where product data was successfully extracted."