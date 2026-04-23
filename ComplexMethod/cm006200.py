def test_model_building_integration(self, mock_chat_openai, component, mock_api_key):
        """Test the complete model building flow."""
        # Mock ChatOpenAI
        mock_instance = MagicMock()
        mock_chat_openai.return_value = mock_instance

        # Configure component
        component.set_attributes(
            {
                "api_key": mock_api_key,
                "model_name": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 1000,
                "seed": 42,
                "json_mode": False,
            }
        )

        # Build model
        model = component.build_model()

        # Verify ChatOpenAI was called correctly
        assert mock_chat_openai.call_count == 1
        _args, kwargs = mock_chat_openai.call_args
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["api_key"] == "test-cometapi-key"
        assert kwargs["max_tokens"] == 1000
        assert kwargs["temperature"] == 0.7
        assert kwargs["model_kwargs"] == {}
        # streaming defaults to None when not explicitly set
        assert kwargs.get("streaming") in (None, False)
        assert kwargs["seed"] == 42
        assert kwargs["base_url"] == "https://api.cometapi.com/v1"
        assert model == mock_instance