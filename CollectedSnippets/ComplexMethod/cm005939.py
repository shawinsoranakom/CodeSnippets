async def test_get_models_with_cloud_and_headers(self, mock_get, mock_post):
        """Test that get_models passes headers for cloud API."""
        component = ChatOllamaComponent()
        component.base_url = DEFAULT_OLLAMA_API_URL
        component.api_key = "test-cloud-api-key"

        mock_get_response = AsyncMock()
        mock_get_response.raise_for_status = MagicMock(return_value=None)
        mock_get_response.json.return_value = {
            component.JSON_MODELS_KEY: [
                {component.JSON_NAME_KEY: "deepseek-v3.1:671b-cloud"},
                {component.JSON_NAME_KEY: "qwen3-coder:480b-cloud"},
            ]
        }
        mock_get.return_value = mock_get_response

        mock_post_response = AsyncMock()
        mock_post_response.raise_for_status = MagicMock(return_value=None)
        mock_post_response.json.side_effect = [
            {component.JSON_CAPABILITIES_KEY: [component.DESIRED_CAPABILITY]},
            {component.JSON_CAPABILITIES_KEY: [component.DESIRED_CAPABILITY]},
        ]
        mock_post.return_value = mock_post_response

        result = await component.get_models(DEFAULT_OLLAMA_API_URL)

        # Verify headers were passed to both GET and POST
        assert mock_get.call_count == 1
        get_call_kwargs = mock_get.call_args[1]
        assert "headers" in get_call_kwargs
        assert get_call_kwargs["headers"]["Authorization"] == "Bearer test-cloud-api-key"

        assert mock_post.call_count == 2
        post_call_kwargs = mock_post.call_args[1]
        assert "headers" in post_call_kwargs
        assert post_call_kwargs["headers"]["Authorization"] == "Bearer test-cloud-api-key"

        assert result == ["deepseek-v3.1:671b-cloud", "qwen3-coder:480b-cloud"]