async def test_deep_crawl_with_llm_extraction(self, async_client: httpx.AsyncClient):
        """Test BFS deep crawl combined with LLMExtractionStrategy."""
        max_depth = 1 # Limit depth to keep LLM calls manageable
        max_pages = 3
        payload = {
            "urls": [DEEP_CRAWL_BASE_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "stream": False,
                    "cache_mode": "BYPASS",
                    "extraction_strategy": { # Apply LLM extraction to crawled pages
                        "type": "LLMExtractionStrategy",
                        "params": {
                            "instruction": "Extract the main H1 title and the text content of the first paragraph.",
                            "llm_config": { # Example override, rely on server default if possible
                               "type": "LLMConfig",
                               "params": {"provider": "openai/gpt-4.1-mini"} # Use a cheaper model for testing
                            },
                             "schema": { # Expected JSON output
                                "type": "dict",
                                "value": {
                                    "title": "PageContent", "type": "object",
                                    "properties": {
                                        "h1_title": {"type": "string"},
                                        "first_paragraph": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "deep_crawl_strategy": {
                        "type": "BFSDeepCrawlStrategy",
                        "params": {
                            "max_depth": max_depth,
                            "max_pages": max_pages,
                            "filter_chain": {
                                "type": "FilterChain",
                                "params": {
                                    "filters": [
                                        {"type": "DomainFilter", "params": {"allowed_domains": [DEEP_CRAWL_DOMAIN]}},
                                        {"type": "ContentTypeFilter", "params": {"allowed_types": ["text/html"]}}
                                    ]
                                }
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
            pytest.fail(f"Deep Crawl + LLM extraction request failed: {e}. Response: {e.response.text}. Check server logs and LLM API key setup.")
        except httpx.RequestError as e:
             pytest.fail(f"Deep Crawl + LLM extraction request failed: {e}.")


        assert data["success"] is True
        assert len(data["results"]) > 0
        assert len(data["results"]) <= max_pages

        found_llm_extraction = False
        for result in data["results"]:
            await assert_crawl_result_structure(result)
            assert result["success"] is True
            assert "extracted_content" in result
            assert result["extracted_content"] is not None
            try:
                extracted = json.loads(result["extracted_content"])
                if isinstance(extracted, list): extracted = extracted[0] # Handle list output
                assert isinstance(extracted, dict)
                assert "h1_title" in extracted # Check keys based on schema
                assert "first_paragraph" in extracted
                found_llm_extraction = True
                print(f"LLM extracted from {result['url']}: Title='{extracted.get('h1_title')}'")
            except (json.JSONDecodeError, AssertionError, IndexError, TypeError) as e:
                pytest.fail(f"LLM extraction validation failed for {result['url']}: {e}\nContent: {result['extracted_content']}")

        assert found_llm_extraction, "LLM extraction did not yield expected data on any crawled page."