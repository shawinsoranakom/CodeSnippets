def test_build_model_with_space_id(self, mock_chatwatsonx, wx_component):
        """Test building model with SpaceID container scope."""
        wx_component.api_key = "test-api-key"  # pragma: allowlist secret
        wx_component.base_url = "https://us-south.ml.cloud.ibm.com"
        wx_component.project_id = None
        wx_component.space_id = "test-space-id"
        wx_component.model_name = "ibm/granite-3-8b-instruct"
        wx_component.stream = True
        wx_component.max_tokens = 2000
        wx_component.temperature = 0.5
        wx_component.top_p = 0.95
        wx_component.frequency_penalty = 0.0
        wx_component.presence_penalty = 0.0
        wx_component.seed = 42
        wx_component.stop_sequence = "END"
        wx_component.logprobs = False
        wx_component.top_logprobs = 5
        wx_component.logit_bias = None

        wx_component.build_model()

        mock_chatwatsonx.assert_called_once()
        call_kwargs = mock_chatwatsonx.call_args[1]

        assert call_kwargs["apikey"] == "test-api-key"  # pragma: allowlist secret
        assert call_kwargs["url"] == "https://us-south.ml.cloud.ibm.com"
        assert call_kwargs["project_id"] is None
        assert call_kwargs["space_id"] == "test-space-id"
        assert call_kwargs["model_id"] == "ibm/granite-3-8b-instruct"
        assert call_kwargs["streaming"] is True
        assert call_kwargs["params"]["stop"] == ["END"]