async def test_llm_extraction(self, async_client: httpx.AsyncClient):
        """
        Test /crawl with LLMExtractionStrategy.
        NOTE: Requires the server to have appropriate LLM API keys (e.g., OPENAI_API_KEY)
              configured via .llm.env or environment variables.
              This test uses the default provider configured in the server's config.yml.
        """
        payload = {
            "urls": [SIMPLE_HTML_URL],
            "browser_config": {"type": "BrowserConfig", "params": {"headless": True}},
            "crawler_config": {
                "type": "CrawlerRunConfig",
                "params": {
                    "cache_mode": CacheMode.BYPASS.value,
                    "extraction_strategy": {
                        "type": "LLMExtractionStrategy",
                        "params": {
                            "instruction": "Extract the main title and the author mentioned in the text into JSON.",
                            # LLMConfig is implicitly defined by server's config.yml and .llm.env
                            # If you needed to override provider/token PER REQUEST:
                            "llm_config": {
                               "type": "LLMConfig",
                               "params": {
                                  "provider": "openai/gpt-4o", # Example override
                                  "api_token": os.getenv("OPENAI_API_KEY") # Example override
                               }
                            },
                            "schema": { # Optional: Provide a schema for structured output
                                "type": "dict", # IMPORTANT: Wrap schema dict
                                "value": {
                                    "title": "Book Info",
                                    "type": "object",
                                    "properties": {
                                        "title": {"type": "string", "description": "The main title of the work"},
                                        "author": {"type": "string", "description": "The author of the work"}
                                    },
                                     "required": ["title", "author"]
                                }
                            }
                        }
                    }
                }
            }
        }

        try:
            response = await async_client.post("/crawl", json=payload)
            response.raise_for_status() # Will raise if server returns 500 (e.g., bad API key)
            data = response.json()
        except httpx.HTTPStatusError as e:
            # Catch potential server errors (like 500 due to missing/invalid API keys)
            pytest.fail(f"LLM extraction request failed: {e}. Response: {e.response.text}. Check server logs and ensure API keys are correctly configured for the server.")
        except httpx.RequestError as e:
             pytest.fail(f"LLM extraction request failed: {e}.")

        assert data["success"] is True
        assert len(data["results"]) == 1
        result = data["results"][0]
        await assert_crawl_result_structure(result)
        assert result["success"] is True
        assert "extracted_content" in result
        assert result["extracted_content"] is not None

        # Extracted content should be JSON (because we provided a schema)
        try:
            extracted_data = json.loads(result["extracted_content"])
            print(f"\nLLM Extracted Data: {extracted_data}") # Print for verification

            # Handle both dict and list formats (server returns a list)
            if isinstance(extracted_data, list):
                assert len(extracted_data) > 0
                extracted_item = extracted_data[0]  # Take first item
                assert isinstance(extracted_item, dict)
                assert "title" in extracted_item
                assert "author" in extracted_item
                assert "Moby-Dick" in extracted_item.get("title", "")
                assert "Herman Melville" in extracted_item.get("author", "")
            else:
                assert isinstance(extracted_data, dict)
                assert "title" in extracted_data
                assert "author" in extracted_data
                assert "Moby-Dick" in extracted_data.get("title", "")
                assert "Herman Melville" in extracted_data.get("author", "")
        except (json.JSONDecodeError, AssertionError) as e:
            pytest.fail(f"LLM extracted content parsing or validation failed: {e}\nContent: {result['extracted_content']}")
        except Exception as e: # Catch any other unexpected error
            pytest.fail(f"An unexpected error occurred during LLM result processing: {e}\nContent: {result['extracted_content']}")