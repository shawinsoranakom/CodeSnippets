def test_get_models_categorizes_llm_and_non_llm(
        self,
        mock_groq,
        mock_get,
        mock_api_key,
        mock_groq_models_response,
        mock_groq_client_tool_calling_success,
        temp_cache_dir,
    ):
        """Test that models are correctly categorized as LLM vs non-LLM."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = mock_groq_models_response
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Mock tool calling tests to always succeed
        mock_groq.return_value = mock_groq_client_tool_calling_success()

        discovery = GroqModelDiscovery(api_key=mock_api_key)
        discovery.CACHE_FILE = temp_cache_dir / ".cache" / "test_cache.json"

        models = discovery.get_models(force_refresh=True)

        # LLM models should be in the result
        assert "llama-3.1-8b-instant" in models
        assert "llama-3.3-70b-versatile" in models
        assert "mixtral-8x7b-32768" in models
        assert "gemma-7b-it" in models

        # Non-LLM models should be marked as not_supported
        assert models["whisper-large-v3"]["not_supported"] is True
        assert models["distil-whisper-large-v3-en"]["not_supported"] is True
        assert models["meta-llama/llama-guard-4-12b"]["not_supported"] is True
        assert models["meta-llama/llama-prompt-guard-2-86m"]["not_supported"] is True

        # LLM models should have tool_calling field
        assert "tool_calling" in models["llama-3.1-8b-instant"]
        assert "tool_calling" in models["mixtral-8x7b-32768"]