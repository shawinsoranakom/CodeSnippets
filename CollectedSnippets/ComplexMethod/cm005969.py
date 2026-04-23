async def test_google_model_creation(self, mock_get_model_class, component_class):
        """Test that the component returns an instance of ChatGoogleGenerativeAI for Google provider."""
        # Setup mock
        mock_google_class = MagicMock()
        mock_instance = MagicMock()
        mock_google_class.return_value = mock_instance
        mock_get_model_class.return_value = mock_google_class

        component = component_class(
            model=[
                {
                    "name": GOOGLE_GENERATIVE_AI_MODELS[0],
                    "provider": "Google Generative AI",
                    "metadata": {
                        "context_length": 32768,
                        "model_class": "ChatGoogleGenerativeAIFixed",
                        "model_name_param": "model",
                        "api_key_param": "google_api_key",
                        "max_tokens_field_name": "max_output_tokens",
                    },
                }
            ],
            api_key="google-test-key",
            temperature=0.7,
            stream=False,
            max_tokens=1000,
        )

        model = component.build_model()

        # Verify the model class getter was called
        mock_get_model_class.assert_called_once_with("ChatGoogleGenerativeAIFixed")

        # Verify the mock was called with max_output_tokens (not max_tokens)
        assert mock_google_class.call_count == 1
        call_kwargs = mock_google_class.call_args[1]
        assert "max_output_tokens" in call_kwargs, "Google should use max_output_tokens"
        assert call_kwargs["max_output_tokens"] == 1000
        assert "max_tokens" not in call_kwargs, "max_tokens should not be used for Google"
        call_kwargs = mock_google_class.call_args[1]

        assert call_kwargs["model"] == GOOGLE_GENERATIVE_AI_MODELS[0]
        assert call_kwargs["temperature"] == 0.7
        assert not call_kwargs["streaming"]
        assert call_kwargs["google_api_key"] == "google-test-key"
        assert model == mock_instance