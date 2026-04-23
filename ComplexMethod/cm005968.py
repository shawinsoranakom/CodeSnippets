async def test_openai_model_creation(self, mock_get_model_class, component_class, default_kwargs):
        """Test that the component returns an instance of ChatOpenAI for OpenAI provider."""
        # Setup mock
        mock_openai_class = MagicMock()
        mock_instance = MagicMock()
        mock_instance.model_name = "gpt-3.5-turbo"
        mock_instance.temperature = 0.5
        mock_instance.streaming = False
        mock_openai_class.return_value = mock_instance
        mock_get_model_class.return_value = mock_openai_class

        # Update default_kwargs to include max_tokens_field_name in metadata
        default_kwargs["model"][0]["metadata"]["max_tokens_field_name"] = "max_tokens"
        default_kwargs["max_tokens"] = 500

        component = component_class(**default_kwargs)
        component.api_key = "sk-test-key"
        component.temperature = 0.5
        component.stream = False

        model = component.build_model()

        # Verify the model class getter was called
        mock_get_model_class.assert_called_once_with("ChatOpenAI")

        # Verify the mock was called with max_tokens
        assert mock_openai_class.call_count == 1
        call_kwargs = mock_openai_class.call_args[1]

        assert call_kwargs["model"] == "gpt-3.5-turbo"
        assert call_kwargs["temperature"] == 0.5
        assert not call_kwargs["streaming"]
        assert call_kwargs["api_key"] == "sk-test-key"
        assert "max_tokens" in call_kwargs, "OpenAI should use max_tokens"
        assert call_kwargs["max_tokens"] == 500
        assert model == mock_instance